import requests
import json
import os

api_key = os.environ.get("GROQ_API_KEY")
if not api_key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "GROQ_API_KEY" in line:
                api_key = line.split("=")[1].strip()

url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    print(f"Fetching models from {url}...")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print("Available Models:")
        for m in models['data']:
            print(f"- {m['id']}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
