
from src import ingestion, synthesis, assets, video
import os
import json

# Manual execution to provide the DELIVERABLE video without needing to click the GUI
print("Starting Manual Generation...")
api_key = os.environ.get("GEMINI_API_KEY")
groq_key = os.environ.get("GROQ_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")

if not api_key or not pexels_key or not groq_key:
    # Try load from .env manually
    if os.path.exists(".env"):
        with open(".env") as f:
             for line in f:
                 if "GEMINI_API_KEY" in line:
                     api_key = line.split("=")[1].strip()
                 elif "PEXELS_API_KEY" in line:
                     pexels_key = line.split("=")[1].strip()
                 elif "GROQ_API_KEY" in line:
                     groq_key = line.split("=")[1].strip()

print(f"Using Gemini Key: {api_key[:10] if api_key else 'None'}...")
print(f"Using Groq Key: {groq_key[:10] if groq_key else 'None'}...")

# 1. Ingestion (Mocked for speed/stability if needed, but lets try fetch)
topic = "Artificial Intelligence trends 2025"
news_item = {"title": topic, "content": f"A comprehensive update on {topic}."}
# Try fetch real news first
try:
    real_news = ingestion.fetch_news_topic("AI")
    if real_news:
        news_item = real_news
        print(f"Fetched: {news_item['title']}")
except:
    print("Fetch failed, using mock.")

# 2. Synthesis
print("Synthesizing script...")
script = synthesis.generate_script(news_item, gemini_key=api_key, groq_key=groq_key)
if not script:
    # Fallback script
    script = {
        "music_mood": "Cyberpunk",
        "segments": [
            {"text": "AI agents are taking over the software world.", "image_prompt": "Futuristic coding robot"},
            {"text": "They can now build entire tools from scratch.", "image_prompt": "Holographic interface being built"},
            {"text": "Generative video is the next big frontier.", "image_prompt": "Cinema camera merging with computer chip"},
            {"text": "The future is automated.", "image_prompt": "Robot hand shaking human hand"}
        ]
    }
    print("Using Fallback script.")

with open("data/manual_script.json", "w") as f:
    json.dump([script], f)

# 3. Assets
print("Generating Assets...")
segments = script.get("segments", [])
assets_dir = "assets"
os.makedirs(assets_dir, exist_ok=True)

for i, seg in enumerate(segments):
    assets.generate_audio(seg['text'], os.path.join(assets_dir, f"{i}_audio.mp3"))
    
    # Visuals: Try Video, then Image
    done = False
    if pexels_key:
        print(f"Searching Pexels for {seg['image_prompt']}...")
        done = assets.search_pexels_video(seg['image_prompt'], os.path.join(assets_dir, f"{i}_visual.mp4"), pexels_key)
    
    if not done:
        print("Fallback to Image Gen...")
        assets.generate_image(seg['image_prompt'], os.path.join(assets_dir, f"{i}_visual.jpg"))
        
    print(f"Segment {i} assets done.")

# 4. Video
print("Rendering Video...")
video.make_video(script, assets_dir, "tool_generated_video.mp4")
print("Done!")
