"""
HuggingFace LLM Service - Su dung HuggingFace Inference API
"""

import requests
import logging
from typing import Dict, List
import time
import os

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """HuggingFace LLM Service"""

    def __init__(self, api_key: str = None, model: str = "MiniMaxAI/MiniMax-M2.5:novita", timeout: int = 120):
        """
        Khoi tao HuggingFace Service

        Args:
            api_key: HF Token (from huggingface.co/settings/tokens)
            model: Model name (VD: MiniMaxAI/MiniMax-M2.5:novita)
            timeout: Thoi gian cho (giay)
        """
        self.api_key = api_key or os.getenv("HF_TOKEN", "")
        self.model = model
        self.timeout = timeout
        self.base_url = "https://router.huggingface.co/v1/chat/completions"
        
        logger.info(f"[HuggingFace] Service khoi tao")
        logger.info(f"[HuggingFace] Model: {self.model}")

    def query(self, messages: List[Dict], max_tokens: int = 2048, temperature: float = 0.7) -> Dict:
        """
        Gui query den HuggingFace API

        Args:
            messages: Danh sach tin nhan [{"role": "user", "content": "..."}]
            max_tokens: So token toi da
            temperature: Nhiet do sinh

        Returns:
            {success, answer, error, latency, method}
        """
        logger.info(f"[HuggingFace] Query (model: {self.model})")
        
        start_time = time.time()
        
        if not self.api_key:
            return {
                "success": False,
                "answer": "HF_TOKEN chua duoc cau hinh",
                "error": "no_api_key",
                "latency": 0,
                "method": "huggingface"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                logger.info(f"[HuggingFace] Thanh cong ({latency:.2f}s)")

                return {
                    "success": True,
                    "answer": answer,
                    "error": None,
                    "latency": latency,
                    "method": "huggingface"
                }
            else:
                return {
                    "success": False,
                    "answer": f"Loi: {response.status_code}",
                    "error": response.text,
                    "latency": latency,
                    "method": "huggingface"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "answer": "Timeout",
                "error": "timeout",
                "latency": time.time() - start_time,
                "method": "huggingface"
            }

        except Exception as e:
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time,
                "method": "huggingface"
            }
