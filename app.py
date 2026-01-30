
import streamlit as st
import os
import json
import time
from src import ingestion, synthesis, assets, video

# Config
DATA_DIR = "data"
ASSETS_DIR = "assets"
REPORTS_DIR = "reports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

st.set_page_config(page_title="Refactored AI Video", page_icon="🎬", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 12, 41, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    
    /* General Text & Labels */
    p, label, .stMarkdown, .stRadio label, .stCheckbox label {
        color: #e0e0e0 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 210, 255, 0.5);
    }
    
    /* Inputs */
    .stTextInput input {
        background-color: #1a1a2e !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stTextInput>div>div {
        background-color: #1a1a2e !important;
        color: #ffffff !important;
    }
    /* Placeholder color */
    ::placeholder {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    /* Hide Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Logo & Title
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=80)
    else:
        st.write("🎬")
with col_title:
    st.title("AI Viral Video Studio")
    st.caption("Create stunning 9:16 vertical videos from trending news or custom topics.")

# Sidebar for Config
# Sidebar for Config
with st.sidebar:
    st.header("Configuration")
    def get_api_key(key_name):
        if key_name in st.secrets:
            return st.secrets[key_name]
        return os.environ.get(key_name, "")

    # Load keys
    default_gemini = get_api_key("GEMINI_API_KEY")
    default_groq = get_api_key("GROQ_API_KEY") 
    default_pexels = get_api_key("PEXELS_API_KEY")

    api_key_input = st.text_input("Gemini API Key", value=default_gemini, type="password")
    groq_key_input = st.text_input("Groq API Key (Optional)", value=default_groq, type="password")
    
    st.info("API Key loaded" if api_key_input or groq_key_input else "Please provide an API Key")

    pexels_key_input = st.text_input("Pexels API Key (Optional for Stock Video)", value=default_pexels, type="password")

    
    use_pexels = st.checkbox("Use Stock Video (Real Footages)", value=True if pexels_key_input else False)

# Main Interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Topic Selection")
    mode = st.radio("Source Mode", ["Custom Topic", "Trending News"])
    
    topic_text = ""
    if mode == "Custom Topic":
        topic_text = st.text_input("Enter a topic:", "Future of AI")
    else:
        if st.button("Fetch Trending Topics"):
            with st.spinner("Scraping Google News..."):
                # Simple fetch of top headline
                news = ingestion.fetch_news_topic("Technology")
                if news:
                    st.success(f"Found: {news['title']}")
                    st.session_state['news_data'] = news
                else:
                    st.error("No news found.")
    
    if mode == "Trending News" and 'news_data' in st.session_state:
        st.json(st.session_state['news_data'])

with col2:
    st.subheader("2. Generation")
    
    if st.button("Generate Video", type="primary"):
        if not api_key_input and not groq_key_input:
            st.error("Missing API Key (Gemini or Groq)")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 1. Content Prep
            status_text.text("Preparing Content...")
            news_item = {}
            if mode == "Trending News" and 'news_data' in st.session_state:
                news_item = st.session_state['news_data']
            else:
                news_item = {"title": topic_text, "content": f"A video about {topic_text}"}
            progress_bar.progress(10)
            
            # 2. Synthesis
            status_text.text("AI Scripting...")
            script = synthesis.generate_script(news_item, gemini_key=api_key_input, groq_key=groq_key_input)
            if not script:
                st.error("Script generation failed.")
                st.stop()
            st.json(script)
            with open(os.path.join(DATA_DIR, "script.json"), "w") as f:
                json.dump([script], f)
            progress_bar.progress(30)
            
            # 3. Assets
            status_text.text("Generating Assets...")
            segments = script.get("segments", [])
            total_segs = len(segments)
            for i, seg in enumerate(segments):
                # Audio
                assets.generate_audio(seg['text'], os.path.join(ASSETS_DIR, f"{i}_audio.mp3"))
                
                # Visuals
                visual_done = False
                if use_pexels and pexels_key_input:
                    # Try Video first
                    status_text.text(f"Searching Pexels for: {seg['image_prompt']}...")
                    visual_done = assets.search_pexels_video(seg['image_prompt'], os.path.join(ASSETS_DIR, f"{i}_visual.mp4"), pexels_key_input)
                
                if not visual_done:
                    # Fallback Image
                    assets.generate_image(seg['image_prompt'], os.path.join(ASSETS_DIR, f"{i}_visual.jpg"))
                
                # Prog update
                current_prog = 30 + int((i+1)/total_segs * 40)
                progress_bar.progress(current_prog)
                
            # 4. Video
            status_text.text("Rendering Video (MoviePy)...")
            output_video = "final_output.mp4"
            success = video.make_video(script, ASSETS_DIR, output_video)
            progress_bar.progress(100)
            
            if success:
                st.success("Video Generated!")
                st.video(output_video)
                
                # Report
                report = f"""# Video Generation Report
**Topic**: {news_item['title']}
**Segments**: {len(segments)}
**Music Mood**: {script.get('music_mood', 'N/A')}

## Script
"""
                for seg in segments:
                    report += f"- {seg['text']} (Visual: {seg['image_prompt']})\n"
                
                with open(os.path.join(REPORTS_DIR, "report.md"), "w") as f:
                    f.write(report)
                
                st.download_button("Download Report", report, "report.md")
            else:
                st.error("Video rendering failed.")
