"""
Cấu hình - đọc từ .env
Đã điều chỉnh cho dự án MEDPILOT_REMIND.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Toàn bộ cấu hình của ứng dụng."""

    # ============ PATHS ============
    BASE_DIR = Path(__file__).parent.parent
    
    DISEASES_JSON = os.getenv("DISEASES_JSON", str(BASE_DIR / "database/data/diseases_data.json"))
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "chroma_db"))
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ============ GOOGLE GEMINI ============
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # ============ LLM - vLLM (Colab) ============
    VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
    VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    
    # ============ SPEECH - Whisper (Colab) ============
    WHISPER_API_URL = os.getenv("WHISPER_API_URL", "http://localhost:8000/v1/audio/transcriptions")
    EXTRACTION_API_URL = os.getenv("EXTRACTION_API_URL", "http://localhost:8000/v1/extract")
    
    # ============ LLM - LOCAL TRANSFORMERS ============
    TRANSFORMERS_MODEL = os.getenv("TRANSFORMERS_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    USE_GPU = os.getenv("USE_GPU", "auto").lower()
    LOAD_4BIT = os.getenv("LOAD_4BIT", "false").lower() == "true"
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))

    # ============ BACKEND ============
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # ============ EMBEDDING ============
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "4"))
    TOP_K = int(os.getenv("TOP_K", "3"))

    # ============ LLM PARAMETERS ============
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
    
    # ============ PERFORMANCE ============
    MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", "50"))
    GC_INTERVAL = int(os.getenv("GC_INTERVAL", "5000"))


settings = Settings()