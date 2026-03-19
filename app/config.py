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
    
    # JSON file (từ convert_text_to_json.py)
    DISEASES_JSON = os.getenv("DISEASES_JSON", str(BASE_DIR / "database/data/diseases_data.json"))
    
    # Vector DB
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "chroma_db"))
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ============ LLM API ============
    # Mặc định Ollama: http://localhost:11434/api/chat
    # Mặc định vLLM:   http://localhost:8001/v1/chat/completions
    LLM_API_URL = os.getenv(
        "LLM_API_URL",
        os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    )
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
    VLLM_MODEL = os.getenv("VLLM_MODEL", OLLAMA_MODEL)

    # ============ CHAT SERVER ============
    CHAT_SERVER_HOST = os.getenv("CHAT_SERVER_HOST", "0.0.0.0")
    CHAT_SERVER_PORT = int(os.getenv("CHAT_SERVER_PORT", "8001"))
    CHAT_API_URL = os.getenv("CHAT_API_URL", "http://localhost:8001/v1/chat/completions")

    # ============ BACKEND ============
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # ============ EMBEDDING ============
    # ⚡ Siêu nhẹ: mô hình 22MB
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "4"))
    TOP_K = int(os.getenv("TOP_K", "1"))  # ⚡ Lấy ít nhất có thể

    # ============ LLM PARAMETERS ============
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))  # ⚡ Giới hạn đầu ra tối thiểu
    NUM_PREDICT = int(os.getenv("NUM_PREDICT", "400"))  # ⚡ Dự đoán tối thiểu
    
    # ============ TỐI ƯU BỘ NHỚ ============
    ENABLE_MODEL_POOLING = os.getenv("ENABLE_MODEL_POOLING", "True").lower() == "true"
    ENABLE_LAZY_LOADING = os.getenv("ENABLE_LAZY_LOADING", "True").lower() == "true"
    MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", "30"))  # ⚡ Cache rất nhỏ
    NUM_CTX = int(os.getenv("NUM_CTX", "2048"))  # ⚡ Ngữ cảnh tối thiểu
    TIMEOUT = int(os.getenv("TIMEOUT", "45"))  # ⚡ Thất bại nhanh
    GC_INTERVAL = int(os.getenv("GC_INTERVAL", "1000"))  # ⚡ Dọn rác mạnh tay
    
    # ============ GIỚI HẠN TÀI NGUYÊN ============
    OLLAMA_NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "0"))  # Chỉ dùng CPU
    OLLAMA_MAX_LOADED_MODELS = int(os.getenv("OLLAMA_MAX_LOADED_MODELS", "1"))


settings = Settings()