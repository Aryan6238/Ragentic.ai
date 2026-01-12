from google import genai
import requests
from app.core.config import settings
import logging
import asyncio
import time

logger = logging.getLogger("uvicorn")

class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = provider or settings.LLM_PROVIDER
        
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not set. Gemini calls will fail.")
            
            # New SDK Initialization
            if settings.GEMINI_API_KEY:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            else:
                self.client = None
                
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash') # Default to 1.5-flash if not set
            self.model_name = model_name
            logger.info(f"Using Gemini model: {model_name}")
            
        elif self.provider == "huggingface":
             if not settings.HF_TOKEN:
                logger.warning("HF_TOKEN not set. Hugging Face calls will fail.")

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates text using the configured provider with retry logic for quota errors.
        """
        full_prompt = f"{system_prompt}\n\nUser Input:\n{user_prompt}"
        max_retries = settings.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                if self.provider == "gemini":
                    if not self.client:
                        return "Error: GEMINI_API_KEY is not set."
                        
                    # specific to Gemini library (google-genai)
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=full_prompt
                    )
                    return response.text
                    
                elif self.provider == "huggingface":
                    # Using inference API (Example URL - would likely need to be configurable in real prod)
                    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
                    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
                    payload = {
                         "inputs": full_prompt,
                         "parameters": {"max_new_tokens": 1024, "return_full_text": False}
                    }
                    response = requests.post(API_URL, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()[0]["generated_text"]
                    
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a quota/rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry delay from error if available, otherwise use exponential backoff
                        retry_delay = 60  # Default 60 seconds
                        if "retry in" in error_str.lower():
                            try:
                                # Try to extract seconds from error message
                                import re
                                match = re.search(r'retry in ([\d.]+)s', error_str.lower())
                                if match:
                                    retry_delay = int(float(match.group(1))) + 5  # Add 5 seconds buffer
                            except:
                                pass
                        
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Quota exceeded. Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"LLM Generation Error (quota exceeded after {max_retries} retries): {error_str}")
                        return f"Error: Quota exceeded. Please wait and try again later, or check your API plan. Details: {error_str[:200]}"
                else:
                    # For non-quota errors, log and return immediately
                    logger.error(f"LLM Generation Error: {error_str}")
                    return f"Error generating response: {error_str[:200]}"
        
        # Should not reach here, but just in case
        return "Error: Failed to generate response after retries."

# Singleton instance
llm_client = LLMClient()
