"""
Service gọi Ollama thông qua Chat Server
"""

import requests
import logging
from typing import Dict, List
import time

logger = logging.getLogger(__name__)


class OllamaService:
    """Gọi Ollama qua Chat Server"""

    def __init__(self, chat_api_url: str, timeout: int = 180):
        """
        Khởi tạo Ollama Service
        
        Args:
            chat_api_url: URL của Chat Server (port 8001)
            timeout: Timeout (giây)
        """
        self.chat_api_url = chat_api_url
        self.timeout = timeout

    def check_health(self) -> bool:
        """Kiểm tra xem Ollama còn sống không"""
        try:
            health_url = self.chat_api_url.replace("/v1/chat/completions", "/health")
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def query(self, messages: List[Dict]) -> Dict:
        """
        Query Ollama qua Chat Server
        
        Args:
            messages: Danh sách messages
        
        Returns:
            {success, answer, error, latency}
        """
        logger.info(f"🤖 Querying Ollama...")

        start_time = time.time()

        try:
            response = requests.post(
                self.chat_api_url,
                json={
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=self.timeout
            )

            latency = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"❌ Error: {response.status_code}")
                return {
                    "success": False,
                    "answer": f"Error: {response.status_code}",
                    "error": response.text,
                    "latency": latency
                }

            answer = response.json()["choices"][0]["message"]["content"]

            logger.info(f"✅ Response ({latency:.2f}s)")

            return {
                "success": True,
                "answer": answer,
                "error": None,
                "latency": latency
            }

        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout")
            return {
                "success": False,
                "answer": "Timeout",
                "error": "timeout",
                "latency": time.time() - start_time
            }

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection Error")
            return {
                "success": False,
                "answer": "Connection Error",
                "error": "connection_error",
                "latency": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "answer": f"Error: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time
            }