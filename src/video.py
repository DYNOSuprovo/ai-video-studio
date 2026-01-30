
import os
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import textwrap

# Monkey Patch for Pillow 10+ if needed
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# Optimization Constants
TARGET_W = 720
TARGET_H = 1280

def create_image_with_text(image_path, text, output_path):
    """
    Draws text onto the image using PIL to avoid ImageMagick dependencies.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # Resize to target if needed
        target_size = (TARGET_W, TARGET_H)
        img = img.resize(target_size, Image.ANTIALIAS)
        
        # Create overlay
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        # Font settings (Default to basic font if custom not found)
        # Scale font size roughly proportional to width (60 for 1080 -> ~40 for 720)
        try:
            # Try load a clean font usually on Windows
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        # Wrap text - Scale width (30 for 1080 -> ~20 for 720 chars? actually font is smaller so char count might be similar)
        # Let's keep 30, it fits
        wrapper = textwrap.TextWrapper(width=30) 
        lines = wrapper.wrap(text)
        
        # Draw Box at bottom
        # Calculate text height
        # Simple estimation: 50px per line (scaled down from 70)
        text_height = len(lines) * 50
        box_top = (TARGET_H - 300) - 20 # Approx position
        box_bottom = box_top + text_height + 40
        
        # Semi-transparent background
        # Scale margin: 50 -> 35
        draw.rectangle([(35, box_top), (TARGET_W - 35, box_bottom)], fill=(0,0,0,160))
        
        # Draw text
        y = box_top + 10
        for line in lines:
            # Center text approximately
            # PIL default font doesn't support getsize well in newer versions, keeping simple
            draw.text((60, y), line, font=font, fill=(255,255,255,255))
            y += 50
            
        # Composite
        out = Image.alpha_composite(img, overlay)
        
        # Only convert to RGB if saving as JPG (which doesn't support alpha)
        # or if explicitly not keeping alpha.
        if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
            out = out.convert("RGB")
        # For PNG, we keep RGBA so it can be used as a transparent overlay
        
        out.save(output_path)
        return True
    except Exception as e:
        print(f"PIL Text Error: {e}")
        return False

def make_video(script_data, assets_dir, output_file):
    clips = []
    segments = script_data.get("segments", [])
    
    for i, seg in enumerate(segments):
        audio_path = os.path.join(assets_dir, f"{i}_audio.mp3")
        visual_img_path = os.path.join(assets_dir, f"{i}_visual.jpg")
        visual_vid_path = os.path.join(assets_dir, f"{i}_visual.mp4")
        titled_visual_path = os.path.join(assets_dir, f"{i}_visual_titled.jpg")
        
        if not os.path.exists(audio_path):
            continue
            
        # Determine Visual Source (Video > Image)
        visual_clip = None
        has_video = os.path.exists(visual_vid_path) and os.path.getsize(visual_vid_path) > 0
        has_image = os.path.exists(visual_img_path)
        
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 0.5 # Padding
            
            if has_video:
                # Load Video
                visual_clip = VideoFileClip(visual_vid_path)
                # Loop if too short, cut if too long
                if visual_clip.duration < duration:
                    visual_clip = vfx.loop(visual_clip, duration=duration)
                visual_clip = visual_clip.subclip(0, duration)
                
                # Resize/Crop to TARGET
                if visual_clip.h != TARGET_H:
                    visual_clip = visual_clip.resize(height=TARGET_H)
                if visual_clip.w > TARGET_W:
                    visual_clip = visual_clip.crop(x1=visual_clip.w/2 - TARGET_W/2, x2=visual_clip.w/2 + TARGET_W/2)
                
                # Force RGB to avoid alpha issues
                visual_clip = visual_clip.to_RGB()

                # Create transparent text overlay using PIL
                # Temp dummy image for sizing
                dummy_path = os.path.join(assets_dir, "temp_size.png")
                Image.new('RGBA', (TARGET_W, TARGET_H), (0,0,0,0)).save(dummy_path)
                overlay_path = os.path.join(assets_dir, f"{i}_overlay.png")
                create_image_with_text(dummy_path, seg['text'], overlay_path)
                 
                # Create Overlay Clip
                overlay_clip = ImageClip(overlay_path, transparent=True).set_duration(duration)
                 
                # Composite: Visual (WebM/MP4) + Overlay (PNG)
                visual_clip = CompositeVideoClip([visual_clip, overlay_clip], size=(TARGET_W, TARGET_H))

            elif has_image:
                # Fallback to Image
                # Burn text into image using PIL
                success = create_image_with_text(visual_img_path, seg['text'], titled_visual_path)
                source_img = titled_visual_path if success else visual_img_path
                visual_clip = ImageClip(source_img).set_duration(duration)
            else:
                continue

            # Common processing
            visual_clip = visual_clip.set_audio(audio_clip)
            visual_clip = visual_clip.fadein(0.5).fadeout(0.5)
            
            # Final Safety Resize
            if visual_clip.h != TARGET_H:
                 visual_clip = visual_clip.resize(height=TARGET_H)
            if visual_clip.w != TARGET_W:
                 visual_clip = visual_clip.crop(x1=visual_clip.w/2 - TARGET_W/2, x2=visual_clip.w/2 + TARGET_W/2)
            
            clips.append(visual_clip)
        except Exception as e:
            print(f"Clip Error {i}: {e}")
            
    if clips:
        # Use compose to fix black screens
        try:
            final_video = concatenate_videoclips(clips, method="compose")
            # OPTIMIZATION: preset="ultrafast", threads=4
            final_video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4)
            
            for c in clips:
                 try: c.close()
                 except: pass
            
            return True
        except Exception as e:
            print(f"Render Error: {e}")
            
    return False
