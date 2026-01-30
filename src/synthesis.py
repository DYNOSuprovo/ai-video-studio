
import os
import json
import time
import google.generativeai as genai

import requests

def generate_script_groq(news_item, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """
    You are a viral video producer. Transform the provided news into a 30-60 second engaging video script.
    Output strictly valid JSON with this schema:
    {
      "music_mood": "string",
      "segments": [
        {"text": "Voiceover sentence here", "image_prompt": "Cinematic shot of ..."},
        ...
      ]
    }
    """
    
    user_prompt = f"""
    News Title: {news_item['title']}
    Content: {news_item['content'][:2000]} ...

    Requirements:
    1. Create 5 to 7 segments. Engaging, hype, but factual.
    2. For each segment, provide a visual prompt for an AI image generator (Pollinations.ai).
    3. Visual prompts should be descriptive, cinematic, and simple.
    """
    
    data = {
        "model": "llama-3.3-70b-versatile", # Valid Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        return json.loads(content)
    except Exception as e:
        print(f"Groq Synthesis failed: {e}")
        return None

def generate_script(news_item, gemini_key=None, groq_key=None):
    # Try Gemini first if key is provided
    if gemini_key:
        print(f"Attempting Gemini generation...")
        args = {"api_key": gemini_key}
        genai.configure(**args)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are a viral video producer. Transform the following news into a 30-60 second engaging video script.
        News Title: {news_item['title']}
        Content: {news_item['content'][:2000]} ...
    
        Requirements:
        1. Create 5 to 7 segments. Engaging, hype, but factual.
        2. For each segment, provide a visual prompt for an AI image generator (Pollinations.ai).
        3. Visual prompts should be descriptive, cinematic, and simple.
        
        Output strictly valid JSON with this schema:
        {{
          "music_mood": "string",
          "segments": [
            {{"text": "Voiceover sentence here", "image_prompt": "Cinematic shot of ..."}},
            ...
          ]
        }}
        """
        
        for attempt in range(3):
            try:
                 response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                 # Clean cleanup if markdown code block is returned (sometimes happens despite mime_type)
                 text = response.text.replace("```json", "").replace("```", "")
                 print("Gemini Success.")
                 return json.loads(text)
            except Exception as e:
                 print(f"Gemini attempt {attempt+1} failed: {e}")
                 time.sleep(2)
        
        print("Gemini failed after retries.")

    # Fallback to Groq
    if groq_key:
        print("Falling back to Groq...")
        result = generate_script_groq(news_item, groq_key)
        if result:
            print("Groq Success.")
            return result
             
    return None
