import os
import json
from src import synthesis

# Test Groq Integration
# Test Groq Integration
groq_key = os.environ.get("GROQ_API_KEY")
if not groq_key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "GROQ_API_KEY" in line:
                groq_key = line.split("=")[1].strip()

news = {"title": "Test News", "content": "This is a test article for Groq generation."}

print("Testing Groq Synthesis...")
script = synthesis.generate_script(news, gemini_key=None, groq_key=groq_key)

if script:
    print("SUCCESS: Script generated!")
    print(json.dumps(script, indent=2))
else:
    print("FAILURE: No script generated.")
