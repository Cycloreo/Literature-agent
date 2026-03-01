import os
import json
from google import genai
from google.genai import types

def analyze_paper_with_gemini(paper_info, api_key, interests_list):
    """
    Evaluates a paper based on a dynamic list of research interests.
    """
    client = genai.Client(api_key=api_key)
    
    # Combine the list of interests into a single formatted string
    formatted_interests = "\n".join([f"- {item}" for item in interests_list])
    
    prompt = f"""
    You are an expert AI assistant for a materials chemistry researcher.
    Evaluate if the following academic paper is highly relevant to any of these core research interests:
    {formatted_interests}

    Paper Title: {paper_info['title']}
    Abstract: {paper_info['abstract']}
    
    Return a JSON object with two keys:
    - "is_relevant": boolean (true or false)
    - "summary": A one-sentence summary of the methodology or breakthrough. Empty string if entirely irrelevant.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        result_json = json.loads(response.text)
        return result_json
        
    except Exception as e:
        print(f"API Error occurred: {e}")
        return {"is_relevant": False, "summary": ""}
    
def deep_analyze_with_gemini(paper_text, api_key):

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a senior materials chemistry expert. I am providing you with the extracted text from an academic paper.
    Please conduct a deep read and extract the following structural information:
    
    1. Background
    2. Methodology
    3. Results analysis
    4. Key Conclusions: A brief summary of the main breakthrough.
    
    Format your response in clean Markdown. Keep it extremely concise and strictly factual.
    
    Paper Text to analyze:
    {paper_text}
    """
    
    try:
        # Using Gemini 3 Flash Preview as it easily handles massive text contexts
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error during deep analysis: {e}"