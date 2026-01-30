#!/usr/bin/env python
# coding: utf-8

# # Stage 4: Composition
# This notebook stitches audio, visuals, and text into a final 9:16 video.

# In[1]:


import json
import os
print("Starting Assembly Script...")

# Monkey Patch for Pillow 10+ / MoviePy 1.0.3
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import *

ASSETS_DIR = "../assets"
DATA_DIR = "../data"

def create_segment_clip(index, segment):
    text = segment.get("text", "")

    # Paths
    audio_path = os.path.join(ASSETS_DIR, f"{index}_audio.mp3")
    visual_path = os.path.join(ASSETS_DIR, f"{index}_visual.jpg")

    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    has_visual = os.path.exists(visual_path) and os.path.getsize(visual_path) > 0

    if not has_visual:
        print(f"Missing visual for segment {index}, skipping.")
        return None

    duration = 5.0 # Default if no audio
    audio_clip = None
    if has_audio:
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
        except Exception as e:
            print(f"Error loading audio {index}: {e}")
            has_audio = False

    # Visual
    visual_clip = ImageClip(visual_path).set_duration(duration)

    # 9:16 Resize and Crop
    visual_clip = visual_clip.resize(height=1920)
    if visual_clip.w > 1080:
        visual_clip = visual_clip.crop(x1=visual_clip.w/2 - 540, x2=visual_clip.w/2 + 540)

    # Text Overlay
    try:
        txt_clip = TextClip(text, fontsize=70, color='white', font='Arial-Bold', method='caption', size=(900, None))
        txt_clip = txt_clip.set_pos('center').set_duration(duration)
        final_clip = CompositeVideoClip([visual_clip, txt_clip])
    except Exception as e:
        print(f"TextClip failed (ImageMagick issue?): {e}")
        final_clip = visual_clip

    if has_audio and audio_clip:
        final_clip = final_clip.set_audio(audio_clip)

    return final_clip

def assemble_video():
    script_path = os.path.join(DATA_DIR, "script.json")
    if not os.path.exists(script_path):
        print("Script not found")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        scripts = json.load(f)

    if not scripts:
        return

    script = scripts[0]
    segments = script.get("segments", [])

    clips = []
    for i, seg in enumerate(segments):
        print(f"Assembling segment {i}...")
        clip = create_segment_clip(i, seg)
        if clip:
            clips.append(clip)

    if clips:
        final_video = concatenate_videoclips(clips)
        final_video.write_videofile("../final_video.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("Video exported to final_video.mp4")

if __name__ == "__main__":
    assemble_video()

