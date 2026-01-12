import google.generativeai as genai
from app.core.config import settings

print(f"Using Key: {settings.GEMINI_API_KEY[:5]}...")
genai.configure(api_key=settings.GEMINI_API_KEY)

try:
    print("Fetching available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
