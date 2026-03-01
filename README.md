🔬 Literature Agent: Automated Research Assistant
An intelligent, 24/7 Discord bot that monitors academic RSS feeds, filters for specific research interests using Gemini AI, and provides structured deep-dives into papers via web scraping or PDF uploads.

🌟 Key Features
1. Automated Daily Push: Scans configured RSS feeds (Nature, ACS, Wiley, etc.) every 24 hours (default: 9:00 AM PST/17:00 UTC) for new articles.
2. AI-Powered Filtering: Uses Gemini 3 Flash to evaluate if new papers match your specific research interests.
3. Structured Summaries: Delivers a concise, one-sentence AI summary of relevant breakthroughs directly to a designated Discord channel.
4. Deep Reading Mode:
   Web-Based: Automatically fetches and analyzes full-text from open-access websites.
   PDF-Based: Support for dragging and dropping PDF files directly into Discord for instant structured analysis (Background, Methodology, Results, Conclusions).
5. Dynamic Configuration: Add or remove RSS feeds and research interests via Discord commands without restarting the bot.
6. Smart Numbering: Papers in the daily push are numbered (e.g., #1, #2) so you can trigger a deep analysis simply by typing !deep 1.

🛠️ Project Structure
literature_agent/
│
├── discord_bot.py       # Main entry point; handles Discord interactions and background tasks
├── config.json          # Stores your RSS feeds and research interest keywords
├── daily_papers.json    # Temporary cache for mapping paper IDs to URLs
│
├── fetcher/             # Module for data acquisition
│   └── rss_parser.py    # Fetches and filters RSS feed entries by date
│
└── llm/                 # Module for AI analysis
    └── gemini_client.py # Interfaces with Gemini API for relevance and deep reading

🚀 Setup & Installation
1. Prerequisites
   Python 3.10+
   A Discord Bot Token (via Discord Developer Portal)
   A Gemini API Key (via Google AI Studio)
2. Install Dependencies
   pip install discord.py requests beautifulsoup4 google-genai feedparser PyMuPDF
3. Replace the following placeholders in discord_bot.py with your credentials:
   BOT_TOKEN: Your Discord bot token.
   GEMINI_API_KEY: Your Google Gemini API key.
   PUSH_CHANNEL_ID: The ID of the Discord channel for paper notifications.

🤖 Discord Commands
Command             Usage                             Description
!list_config     !list_config              Displays current RSS feeds and interests.
!add_interest    !add_interest <keyword>   Adds a new topic to monitor.
!add_rss         !add_rss <url>            Adds a new journal RSS feed.
!force_push      !force_push               Manually triggers the daily scan immediately.
!deep            !deep <ID>                Deeply analyzes a paper from the daily list by its ID.
!deep            !deep (+ PDF File)        Analyzes a PDF file you drag-and-drop into the chat.

☁️ Deployment Note (AWS)
To run this agent 24/7 on an AWS EC2 instance (Ubuntu):
1. Set up a Virtual Environment: python3 -m venv venv && source venv/bin/activate.
2. Use Screen to keep it running after logout:
    screen -S paper_bot
    python3 discord_bot.py
    # Press Ctrl+A then D to detach

📜 License
This project is intended for academic research assistance. Please ensure compliance with journal terms of service when using scraping features.
