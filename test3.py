import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

for model in ["gemini-1.5-flash", "gemini-2.0-flash"]:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Say hi"
        )
        print(f"{model}: Success: {response.text.strip()}")
    except Exception as e:
        print(f"{model}: Error: {e}")
