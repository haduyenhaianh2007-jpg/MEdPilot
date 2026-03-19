"""
Chat Server - Wrapper cho Ollama
Chạy trên port 8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging
import os
from typing import List, Optional, Dict
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedPilot Chat Server",
    description="Ollama Qwen 2.5 7B Wrapper",
    version="1.0"
)

# ============ CONFIG ============
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
TIMEOUT = int(os.getenv("TIMEOUT", "180"))

logger.info(f"📍 Ollama: {OLLAMA_URL}")
logger.info(f"🧠 Model: {MODEL}\n")

# ============ MODELS ============
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: int = 1000
    temperature: Optional[float] = 0.7
    stream: bool = False


class ChatResponse(BaseModel):
    choices: List[Dict]
    model: str
    usage: Optional[Dict] = None


# ============ ENDPOINTS ============
@app.post("/v1/chat/completions", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Chat completion endpoint
    OpenAI compatible format
    """

    logger.info(f"📨 Chat: {len(req.messages)} messages")

    start_time = time.time()

    try:
        # Convert to dict
        messages = [{"role": m.role, "content": m.content} for m in req.messages]

        logger.info(f"🚀 Querying {MODEL}...")

        # Forward to Ollama
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": messages,
                "stream": req.stream,
                "options": {
                    "num_predict": req.max_tokens,
                    "num_ctx": 16384,
                    "temperature": req.temperature,
                }
            },
            timeout=TIMEOUT
        )

        # Check status
        if response.status_code != 200:
            logger.error(f"❌ Ollama error: {response.status_code}")
            raise HTTPException(
                status_code=502,
                detail=f"Ollama error: {response.status_code}"
            )

        ollama_response = response.json()
        content = ollama_response.get("message", {}).get("content", "")

        if not content:
            logger.error("❌ Empty response")
            raise HTTPException(status_code=502, detail="Empty response")

        latency = time.time() - start_time

        logger.info(f"✅ Response ({latency:.2f}s)")

        # Return OpenAI format
        return ChatResponse(
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            model=MODEL,
            usage={
                "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                "completion_tokens": ollama_response.get("eval_count", 0),
                "total_tokens": ollama_response.get("prompt_eval_count", 0) +
                               ollama_response.get("eval_count", 0)
            }
        )

    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout")
        raise HTTPException(status_code=504, detail="Ollama timeout")

    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection Error")
        raise HTTPException(status_code=503, detail="Ollama offline")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check"""
    try:
        response = requests.get(
            OLLAMA_URL.replace("/api/chat", ""),
            timeout=5
        )
        ollama_ok = response.status_code == 200
    except:
        ollama_ok = False

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "ollama": "connected" if ollama_ok else "disconnected"
    }


@app.get("/v1/models")
def list_models():
    """List models"""
    return {
        "object": "list",
        "data": [{
            "id": MODEL,
            "object": "model",
            "owned_by": "ollama",
            "created": int(datetime.now().timestamp())
        }]
    }


@app.get("/info")
def info():
    """Server info"""
    return {
        "name": "MedPilot Chat Server",
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
        "endpoints": {
            "chat": "/v1/chat/completions",
            "health": "/health",
            "models": "/v1/models"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print(f"\n{'='*50}")
    print(f"🚀 Chat Server")
    print(f"{'='*50}")
    print(f"🧠 Model: {MODEL}")
    print(f"🌐 http://0.0.0.0:8001")
    print(f"{'='*50}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )