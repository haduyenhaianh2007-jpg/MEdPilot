"""
Claude LLM Service - Tich hop Anthropic Claude API
"""

import requests
import logging
from typing import Dict, List, Optional
import time
import os

logger = logging.getLogger(__name__)


class ClaudeService:
    """Claude LLM Service - GoI Anthropic Claude API"""

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514", timeout: int = 120):
        """
        Khoi tao Claude Service

        Args:
            api_key: Anthropic API Key
            model: Model name (default: claude-sonnet-4-20250514)
            timeout: Thoi gian cho (giay)
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1/messages"
        
        if not self.api_key:
            logger.warning("Khong tim thay CLAUDE_API_KEY!")
        
        logger.info(f"[Claude] Service khoi tao voi model: {self.model}")

    def query(self, messages: List[Dict], max_tokens: int = 1024, temperature: float = 0.7) -> Dict:
        """
        Gui query den Claude API

        Args:
            messages: Danh sach tin nhan (OpenAI format)
            max_tokens: So token toi da
            temperature: Nhiet do sinh

        Returns:
            {success, answer, error, latency, method}
        """
        logger.info(f"[Claude] Query (model: {self.model}, max_tokens: {max_tokens})")
        
        start_time = time.time()
        
        if not self.api_key:
            return self._fallback_response(messages, start_time, "API key missing")
        
        # Chuyen doi messages sang Claude format
        anthropic_messages = self._convert_messages(messages)
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
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
                answer = data.get("content", [{}])[0].get("text", "")
                
                logger.info(f"[Claude] Thanh cong ({latency:.2f}s)")
                
                return {
                    "success": True,
                    "answer": answer,
                    "error": None,
                    "latency": latency,
                    "method": "claude"
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"[Claude] Loi: {error_msg}")
                
                return {
                    "success": False,
                    "answer": f"Loi API: {response.status_code}",
                    "error": error_msg,
                    "latency": latency,
                    "method": "claude"
                }
                
        except requests.exceptions.Timeout:
            latency = time.time() - start_time
            logger.error(f"[Claude] Timeout ({self.timeout}s)")
            
            return {
                "success": False,
                "answer": "Claude Timeout - qua tre",
                "error": "timeout",
                "latency": latency,
                "method": "claude"
            }
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[Claude] Exception: {str(e)}")
            
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": latency,
                "method": "claude"
            }

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Chuyen doi OpenAI format sang Claude format
        
        OpenAI: [{"role": "system/user/assistant", "content": "..."}]
        Claude: [{"role": "user/assistant", "content": [{"type": "text", "text": "..."}]}]
        """
        anthropic_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Claude khong co system role, ghep vao first user message
            if role == "system":
                # Add system instruction as first user message
                if anthropic_messages and anthropic_messages[0]["role"] == "user":
                    anthropic_messages[0]["content"] = [{"type": "text", "text": f"{content}\n\n{anthropic_messages[0]['content'][0]['text']}"}]
                continue
            
            # Map roles
            if role == "assistant":
                claude_role = "assistant"
            else:
                claude_role = "user"
            
            anthropic_messages.append({
                "role": claude_role,
                "content": [{"type": "text", "text": content}]
            })
        
        return anthropic_messages

    def _fallback_response(self, messages: List[Dict], start_time: float, reason: str) -> Dict:
        """Fallback khi khong goi duoc API"""
        latency = time.time() - start_time
        
        fallback = f"""
[CLAUDE FALLBACK MODE]

Khong the goi Claude API: {reason}

De su dung Claude:
1. Lay API key tu https://console.anthropic.com
2. Them vao .env: CLAUDE_API_KEY=your_key
3. Restart backend
"""
        
        logger.warning(f"[Claude] Su dung fallback: {reason}")
        
        return {
            "success": False,
            "answer": fallback,
            "error": reason,
            "latency": latency,
            "method": "claude_fallback"
        }

    def test_connection(self) -> bool:
        """Test ket noi API"""
        result = self.query(
            [{"role": "user", "content": "Hello"}],
            max_tokens=50
        )
        return result.get("success", False)
