"""
Ollama LLM Service - GoI Ollama API
"""

import requests
import logging
from typing import Dict, List
import time
import os

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama LLM Service"""

    def __init__(self, api_url: str = None, model: str = "qwen2.5:7b", timeout: int = 120):
        """
        Khoi tao Ollama Service

        Args:
            api_url: URL Ollama server (VD: http://localhost:11434/api/chat)
            model: Model name (VD: qwen2.5:7b)
            timeout: Thoi gian cho (giay)
        """
        self.api_url = api_url or os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
        self.model = model
        self.timeout = timeout
        self.is_available = self._check_availability()
        
        logger.info(f"[Ollama] Service khoi tao voi model: {self.model}")
        logger.info(f"[Ollama] URL: {self.api_url}")
        if self.is_available:
            logger.info(f"[Ollama] Server dang hoat dong")
        else:
            logger.warning(f"[Ollama] Server khong kha dung")

    def _check_availability(self) -> bool:
        """Kiem tra server co san khong"""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def query(self, messages: List[Dict], max_tokens: int = 2048, temperature: float = 0.7) -> Dict:
        """
        Gui query den Ollama

        Args:
            messages: Danh sach tin nhan [{"role": "user", "content": "..."}]
            max_tokens: So token toi da
            temperature: Nhiet do sinh

        Returns:
            {success, answer, error, latency, method}
        """
        logger.info(f"[Ollama] Query (model: {self.model})")
        
        start_time = time.time()
        
        if not self.is_available:
            return self._fallback_response(start_time)

        # Chuyen doi messages
        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens
            }
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )

            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                answer = data.get("message", {}).get("content", "")

                logger.info(f"[Ollama] Thanh cong ({latency:.2f}s)")

                return {
                    "success": True,
                    "answer": answer,
                    "error": None,
                    "latency": latency,
                    "method": "ollama"
                }
            else:
                return {
                    "success": False,
                    "answer": f"Loi: {response.status_code}",
                    "error": response.text,
                    "latency": latency,
                    "method": "ollama"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "answer": "Timeout",
                "error": "timeout",
                "latency": time.time() - start_time,
                "method": "ollama"
            }

        except Exception as e:
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time,
                "method": "ollama"
            }

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """Chuyen doi messages, loai bo system"""
        ollama_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Ollama dung "assistant" thay "assistant"
            if role == "assistant":
                role = "assistant"
            elif role == "system":
                continue  # Bo system messages
            else:
                role = "user"
            
            ollama_messages.append({
                "role": role,
                "content": content
            })
        
        return ollama_messages

    def _fallback_response(self, start_time: float) -> Dict:
        """Fallback khi server khong kha dung"""
        return {
            "success": False,
            "answer": "Ollama server khong kha dung. Chay 'ollama serve' truoc.",
            "error": "server_not_available",
            "latency": time.time() - start_time,
            "method": "ollama"
        }
