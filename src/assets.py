
import os
import requests
import edge_tts
import asyncio
from mutagen.mp3 import MP3

async def _generate_audio_async(text, output_file, voice="en-US-GuyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_audio(text, output_file):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_audio_async(text, output_file))
        loop.close()
        return True
    except Exception as e:
        print(f"TTS Error: {e}")
        return False

def get_audio_duration(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length
    except:
        return 0

def generate_image(prompt, output_file):
    # Pollinations.ai simple GET request
    # Enforce vertical 9:16 aspect ratio (1080x1920)
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&nologo=true"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Image Gen Error: {e}")
    return False

def search_pexels_video(query, output_file, api_key):
    if not api_key:
        return False
        
    headers = {"Authorization": api_key}
    # Search for vertical videos (portrait)
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1&size=medium"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("videos"):
            video_files = data["videos"][0]["video_files"]
            # specific logic to find best quality MP4 compatible with moviepy
            # usually the one with width <= 1080 to save bandwidth but good quality
            best_video = None
            for v in video_files:
                if v["file_type"] == "video/mp4" and v["width"] <= 1080:
                    best_video = v
                    break
            
            if not best_video:
                 best_video = video_files[0] # Fallback
            
            # Download
            link = best_video["link"]
            v_response = requests.get(link, stream=True)
            with open(output_file, 'wb') as f:
                for chunk in v_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True
            
    except Exception as e:
        print(f"Pexels Error: {e}")
        
    return False
