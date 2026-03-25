"""
Dịch vụ LLM - gọi Ollama, vLLM hoặc cơ chế dự phòng.
"""

import requests
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class LLMService:
    """Dịch vụ LLM - tương thích với Ollama, vLLM hoặc chế độ dự phòng."""

    def __init__(self, api_url: str, model: str, timeout: int = 180, check_on_init: bool = False):
        """
        Khởi tạo dịch vụ LLM.

        Tham số:
            api_url: URL API LLM (Ollama hoặc vLLM)
            model: Tên mô hình
            timeout: Thời gian chờ, tính bằng giây
            check_on_init: Có kiểm tra availability ngay không (mặc định False để tránh blocking)
        """
        self.api_url = api_url
        self.model = model
        self.timeout = timeout
        self.is_available = False
        self.is_vllm = self._is_vllm_endpoint(api_url)
        
        if check_on_init:
            self._check_availability()
        else:
            logger.info(f"⏭️  Skipping availability check on init (lazy check on first query)")

    def _is_vllm_endpoint(self, url: str) -> bool:
        """Nhận diện endpoint vLLM tương thích chuẩn OpenAI."""
        return "/v1/chat/completions" in url or "/v1/completions" in url

    def _check_availability(self) -> bool:
        """Kiểm tra backend có sẵn sàng không, không làm treo lúc khởi động."""
        try:
            response = requests.post(
                self.api_url,
                json=self._build_payload([{"role": "user", "content": "test"}], 1),
                timeout=30
            )
            self.is_available = response.status_code == 200
            
            if self.is_available:
                backend_name = "vLLM" if self.is_vllm else "Ollama"
                logger.info(f"✅ {backend_name} available at {self.api_url}")
            else:
                logger.warning(f"❌ LLM backend returned status {response.status_code}")
                logger.info(f"   Server will use fallback responses")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️  LLM backend timeout (too slow)")
            logger.info(f"   Check: {self.api_url}")
            self.is_available = False
        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️  LLM backend not available at {self.api_url}")
            logger.info(f"   Start Ollama or vLLM server")
            self.is_available = False
        except Exception as e:
            logger.warning(f"⚠️  Error checking LLM backend: {str(e)}")
            self.is_available = False
        
        return self.is_available

    def _build_payload(self, messages: List[Dict], max_tokens: int) -> Dict:
        """Tạo payload yêu cầu cho Ollama hoặc vLLM."""
        if self.is_vllm:
            return {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": max_tokens,
                "stream": False,
            }

        return {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.9,
                "num_predict": max_tokens
            }
        }

    def query(self, messages: List[Dict], max_tokens: int = 1000) -> Dict:
        """
        Gửi truy vấn đến LLM.

        Tham số:
            messages: Danh sách tin nhắn
            max_tokens: Số token tối đa

        Trả về:
            {success, answer, error, method}
        """
        backend_name = "vLLM" if self.is_vllm else "Ollama"
        
        if not self.is_available:
            logger.info(f"🤖 LLM not checked yet, doing lazy availability check...")
            self._check_availability()
        
        logger.info(f"🤖 LLM Query (method: {backend_name if self.is_available else 'Fallback'})")

        start_time = time.time()

        if self.is_available:
            if self.is_vllm:
                return self._query_vllm(messages, max_tokens, start_time)
            return self._query_ollama(messages, max_tokens, start_time)
        else:
            return self._query_fallback(messages, start_time)

    def _query_vllm(self, messages: List[Dict], max_tokens: int, start_time: float) -> Dict:
        """Gọi API vLLM theo chuẩn tương thích OpenAI."""
        try:
            response = requests.post(
                self.api_url,
                json=self._build_payload(messages, max_tokens),
                timeout=self.timeout
            )

            latency = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"❌ vLLM error: {response.status_code}")
                return {
                    "success": False,
                    "answer": f"LLM Error: {response.status_code}",
                    "error": response.text,
                    "latency": latency,
                    "method": "vllm"
                }

            data = response.json()
            choices = data.get("choices", [])
            answer = choices[0].get("message", {}).get("content", "No response") if choices else "No response"

            logger.info(f"✅ vLLM response ({latency:.2f}s)")

            return {
                "success": True,
                "answer": answer,
                "error": None,
                "latency": latency,
                "method": "vllm"
            }

        except requests.exceptions.Timeout:
            logger.error(f"❌ vLLM timeout")
            return {
                "success": False,
                "answer": "LLM Timeout",
                "error": "timeout",
                "latency": time.time() - start_time,
                "method": "vllm"
            }

        except Exception as e:
            logger.error(f"❌ vLLM error: {str(e)}")
            return {
                "success": False,
                "answer": f"LLM Error: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time,
                "method": "vllm"
            }

    def _query_ollama(self, messages: List[Dict], max_tokens: int, start_time: float) -> Dict:
        """Gọi trực tiếp Ollama."""
        try:
            response = requests.post(
                self.api_url,
                json=self._build_payload(messages, max_tokens),
                timeout=self.timeout
            )

            latency = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"❌ Ollama error: {response.status_code}")
                return {
                    "success": False,
                    "answer": f"LLM Error: {response.status_code}",
                    "error": response.text,
                    "latency": latency,
                    "method": "ollama"
                }

            data = response.json()
            answer = data.get("message", {}).get("content", "No response")

            logger.info(f"✅ Ollama response ({latency:.2f}s)")

            return {
                "success": True,
                "answer": answer,
                "error": None,
                "latency": latency,
                "method": "ollama"
            }

        except requests.exceptions.Timeout:
            logger.error(f"❌ Ollama timeout")
            return {
                "success": False,
                "answer": "LLM Timeout",
                "error": "timeout",
                "latency": time.time() - start_time,
                "method": "ollama"
            }

        except Exception as e:
            logger.error(f"❌ Ollama error: {str(e)}")
            return {
                "success": False,
                "answer": f"LLM Error: {str(e)}",
                "error": str(e),
                "latency": time.time() - start_time,
                "method": "ollama"
            }

    def _query_fallback(self, messages: List[Dict], start_time: float) -> Dict:
        """Chế độ dự phòng - tạo phản hồi từ context có sẵn."""
        latency = time.time() - start_time
        
        # Lấy nội dung của tin nhắn người dùng
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Tạo phản hồi dự phòng
        backend_name = "vLLM" if self.is_vllm else "Ollama"
        fallback_response = f"""
    ⚠️ **LLM SERVICE NOT AVAILABLE (Fallback Mode)**

    Không thể kết nối {backend_name} tại {self.api_url}

**Để sử dụng LLM:**
    1. Với Ollama: cài Ollama và chạy `ollama serve`
    2. Với vLLM: chạy server OpenAI-compatible trên Linux/WSL2
    3. Pull/load model phù hợp với backend đang dùng

**Dữ liệu medical đã được retrieve thành công**
Dùng context từ Vector DB để cung cấp thông tin.

**Lưu ý:** Response này chỉ dựa trên retrieved information, 
không có xử lý AI từ LLM.
"""
        
        logger.warning(f"⚠️  Using fallback mode (no LLM)")

        return {
            "success": False,
            "answer": fallback_response,
            "error": "llm_not_available",
            "latency": latency,
            "method": "fallback"
        }
