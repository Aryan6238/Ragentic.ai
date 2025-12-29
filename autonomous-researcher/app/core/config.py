import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = ""
    HF_TOKEN: str = ""
    
    # Configuration
    LLM_PROVIDER: str = "gemini"
    GEMINI_MODEL: str = "gemini-flash-latest"  # Using latest flash model (auto-updates to best available)
    MAX_RETRIES: int = 3
    LOG_LEVEL: str = "INFO"
    
    # Project Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
