"""
vLLM LLM Service - GoI vLLM/OpenAI-compatible API
"""

import requests
import logging
from typing import Dict, List
import time
import os

logger = logging.getLogger(__name__)


class vLLMService:
    """vLLM LLM Service - OpenAI-compatible API"""

    def __init__(self, api_url: str = None, model: str = "Qwen/Qwen2.5-1.5B-Instruct", timeout: int = 120):
        """
        Khoi tao vLLM Service

        Args:
            api_url: URL vLLM server (VD: https://xxx.ngrok.io/v1/chat/completions)
            model: Model name
            timeout: Thoi gian cho (giay)
        """
        self.api_url = api_url or os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
        self.model = model
        self.timeout = timeout
        
        logger.info(f"[vLLM] Service khoi tao")
        logger.info(f"[vLLM] URL: {self.api_url}")
        logger.info(f"[vLLM] Model: {self.model}")

    def query(self, messages: List[Dict], max_tokens: int = 2048, temperature: float = 0.7) -> Dict:
        """
        Gui query den vLLM

        Args:
            messages: Danh sach tin nhan [{"role": "user", "content": "..."}]
            max_tokens: So token toi da
            temperature: Nhiet do sinh

        Returns:
            {success, answer, error, latency, method}
        """
        logger.info(f"[vLLM] Query (model: {self.model})")
        
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "MedPilot-Backend/1.0"
                }
            )

            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                logger.info(f"[vLLM] Thanh cong ({latency:.2f}s)")

                return {
                    "success": True,
                    "answer": answer,
                    "error": None,
                    "latency": latency,
                    "method": "vllm"
                }
            elif response.status_code == 404:
                logger.error(f"[vLLM] 404 Not Found - Ngrok URL co the het han: {self.api_url}")
                return {
                    "success": False,
                    "answer": "⚠️ Lỗi kết nối AI (404): URL Ngrok đã hết hạn hoặc Colab chưa chạy. Vui lòng cập nhật VLLM_API_URL trong file .env rồi restart backend.",
                    "error": f"404 Not Found - URL: {self.api_url}",
                    "latency": latency,
                    "method": "vllm"
                }
            else:
                logger.error(f"[vLLM] Loi {response.status_code}: {response.text[:200]}")
                return {
                    "success": False,
                    "answer": f"⚠️ Lỗi kết nối AI ({response.status_code}). Vui lòng thử lại.",
                    "error": response.text[:500],
                    "latency": latency,
                    "method": "vllm"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "answer": "Timeout",
                "error": "timeout",
                "latency": time.time() - start_time,
                "method": "vllm"
            }

        except Exception as e:
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time,
                "method": "vllm"
            }

    def test_connection(self) -> bool:
        """Test ket noi"""
        result = self.query(
            [{"role": "user", "content": "Hello"}],
            max_tokens=50
        )
        return result.get("success", False)
