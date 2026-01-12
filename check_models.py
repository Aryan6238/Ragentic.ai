from google import genai
from app.core.config import settings

print(f"Using Key: {settings.GEMINI_API_KEY[:5]}...")
if not settings.GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY is not set. Skipping real API connectivity check.")
    # We can still check if the module imports correctly, which it does if we reached here.
    client = None
else:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

try:
    # Verify other critical imports
    print("Verifying imports...")
    from app.services.vector_db import vector_db
    print("✅ VectorDB (ChromaDB) imported successfully.")
    
    from app.core.llm import llm_client
    print("✅ LLM Client imported successfully.")

    if client:
        print("Fetching available models...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello"
        )
        print("✅ Successfully connected to Gemini API!")
        print(f"Response: {response.text}")
    else:
        print("⚠️  Skipping API connection check (KEY missing). Imports Verified.")
    
except Exception as e:
    print(f"❌ Error: {e}")
