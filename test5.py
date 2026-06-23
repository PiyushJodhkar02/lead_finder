import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

test_models = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp"
]

for model in test_models:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Say hi"
        )
        print(f"Success with {model}: {response.text.strip()}")
    except Exception as e:
        print(f"Failed with {model}: {e}")
