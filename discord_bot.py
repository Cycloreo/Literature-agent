import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import datetime
import fitz  # PyMuPDF library for reading PDF files
import io

# Import your custom modules
from llm.gemini_client import deep_analyze_with_gemini, analyze_paper_with_gemini
from fetcher.rss_parser import fetch_latest_papers

# ==========================================
# 1. Configuration & Storage Setup
# ==========================================
CONFIG_FILE = "config.json"
PAPERS_CACHE_FILE = "daily_papers.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"rss_feeds": [], "research_interests": []}

def save_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)

def save_daily_papers(papers_dict):
    with open(PAPERS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(papers_dict, f, indent=4)

def load_daily_papers():
    try:
        with open(PAPERS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def extract_text_from_pdf(pdf_bytes):
    """Extracts text from a PDF file stream using PyMuPDF."""
    text = ""
    try:
        # Open the PDF from memory
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text("text") + "\n"
        pdf_document.close()
    except Exception as e:
        print(f"[SYSTEM] Error extracting PDF text: {e}")
    
    return text

# ==========================================
# 2. Bot Initialization
# ==========================================
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

PUSH_CHANNEL_ID = int(os.environ.get("DISCORD_PUSH_CHANNEL_ID", "123456789012345678"))

# ==========================================
# 3. Automated Background Tasks
# ==========================================
target_time = datetime.time(hour=9, minute=0, second=0)

@tasks.loop(time=target_time)
async def daily_paper_push():
    channel = bot.get_channel(PUSH_CHANNEL_ID)
    if not channel:
        print(f"[SYSTEM] Error: Could not find channel with ID {PUSH_CHANNEL_ID}.")
        return

    print("[SYSTEM] Starting automated daily paper analysis...")
    config = load_config()
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "API_key")

    if not config.get("rss_feeds"):
        print("[SYSTEM] No RSS feeds configured.")
        return

    total_relevant = 0
    paper_id_counter = 1
    daily_papers_cache = {}

    for rss_url in config.get("rss_feeds", []):
        print(f"[FETCH] Scanning: {rss_url}")
        papers = await asyncio.to_thread(fetch_latest_papers, rss_url, days_to_look_back=1)

        if not papers:
            continue

        for paper in papers:
            analysis = await asyncio.to_thread(
                analyze_paper_with_gemini, paper, gemini_api_key, config.get("research_interests", [])
            )

            if analysis.get('is_relevant'):
                total_relevant += 1
                summary = analysis.get('summary', 'No summary provided by AI.')
                
                daily_papers_cache[str(paper_id_counter)] = paper['link']

                message = f"🚨 **Revelent Paper #{paper_id_counter}** \n\n" \
                          f"**Title:** {paper['title']}\n" \
                          f"**Published:** {paper['published']}\n\n" \
                          f"**AI Summary:** {summary}\n\n" \
                          f"🔗 [Read Full Article]({paper['link']})\n" \
                          f"*(Reply with `!deep {paper_id_counter}` or drag and drop a PDF file with `!deep`)*"
                
                await channel.send(message)
                paper_id_counter += 1
                await asyncio.sleep(3) 

    save_daily_papers(daily_papers_cache)
    print(f"[SYSTEM] Daily push completed. Found {total_relevant} papers.")

@daily_paper_push.before_loop
async def before_daily_push():
    await bot.wait_until_ready()

# ==========================================
# 4. Interactive Commands
# ==========================================
@bot.event
async def on_ready():
    print(f'[SYSTEM] Logged in successfully as {bot.user.name}!')
    if not daily_paper_push.is_running():
        daily_paper_push.start()

@bot.command(name='force_push')
async def force_push(ctx):
    await ctx.send("⚙️ Manual push triggered. Processing feeds in the background...")
    asyncio.create_task(daily_paper_push())

@bot.command(name='list_config')
async def list_config(ctx):
    config = load_config()
    feeds = "\n".join([f"- {url}" for url in config.get("rss_feeds", [])])
    interests = "\n".join([f"- {item}" for item in config.get("research_interests", [])])
    await ctx.send(f"**📡 Monitored RSS Feeds:**\n{feeds}\n\n**🔬 Research Interests:**\n{interests}")

@bot.command(name='add_interest')
async def add_interest(ctx, *, interest: str):
    config = load_config()
    if interest not in config.get("research_interests", []):
        config.setdefault("research_interests", []).append(interest)
        save_config(config)
        await ctx.send(f"✅ Research interest added: **{interest}**")

@bot.command(name='deep')
async def deep_read(ctx, paper_id: str = None):
    """Deep reads a paper from an uploaded PDF or daily ID number."""
    
    extracted_text = ""
    gemini_key = os.environ.get("GEMINI_API_KEY", "API_key")

    # Scenario 1: User uploaded a PDF file
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.lower().endswith('.pdf'):
            await ctx.send(f"📥 Receiving PDF: `{attachment.filename}`...\n*Extracting text and running deep analysis. Please wait...*")
            try:
                # Read the file directly from Discord's servers into memory
                pdf_bytes = await attachment.read()
                extracted_text = await asyncio.to_thread(extract_text_from_pdf, pdf_bytes)
                
                if not extracted_text.strip():
                    await ctx.send("⚠️ Failed to extract text. The PDF might be image-based (scanned) without OCR.")
                    return
            except Exception as e:
                await ctx.send(f"❌ Error processing the PDF file: {e}")
                return
        else:
            await ctx.send("⚠️ Please upload a valid `.pdf` document for analysis.")
            return

    # Scenario 2: User provided a paper ID from the daily push
    elif paper_id:
        cache = load_daily_papers()
        if paper_id not in cache:
            await ctx.send(f"⚠️ Error: Could not find paper ID `{paper_id}`. Please check the number.")
            return

        target_url = cache[paper_id]
        await ctx.send(f"⏳ Initiating web analysis for Paper #{paper_id}...\n*Target: {target_url}*")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        try:
            response = await asyncio.to_thread(requests.get, target_url, headers=headers, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            extracted_text = soup.get_text(separator=' ', strip=True)

            if len(extracted_text) < 800:
                await ctx.send(f"⚠️ **Hit a Paywall!** Only {len(extracted_text)} characters were extracted.\n"
                               f"**Solution:** Please download the full PDF from your university library, drag and drop it into this chat, and type `!deep` as the message.")
                return
        except Exception as e:
            await ctx.send(f"❌ Network error while fetching the paper: {e}")
            return
            
    # Scenario 3: User typed !deep with no ID and no attachment
    else:
        await ctx.send("⚠️ Invalid command. Please either provide a daily paper ID (e.g., `!deep 1`) OR upload a PDF file and type `!deep` in the comment box.")
        return

    # Common Step: Send the extracted text to Gemini
    try:
        # Limit to 80,000 characters to prevent token overflow
        extracted_text = extracted_text[:80000] 
        summary_result = await asyncio.to_thread(deep_analyze_with_gemini, extracted_text, gemini_key)

        if len(summary_result) > 1900:
            summary_result = summary_result[:1900] + "\n\n*[Result truncated due to Discord message limits]*"

        await ctx.send(f"**🔬 Deep Analysis Report:**\n\n{summary_result}")
    except Exception as e:
        await ctx.send(f"❌ An error occurred during AI analysis: {e}")

# ==========================================
# 5. Program Execution
# ==========================================
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "BOT_token")
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        print("[SYSTEM] Critical Error: Please set your Discord Bot Token.")
    else:
        bot.run(BOT_TOKEN)