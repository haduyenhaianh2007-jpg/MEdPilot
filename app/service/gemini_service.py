"""
Gemini LLM Service - Tich hop Google Gemini 2.5 Flash API
Thay the Ollama/vLLM service
"""

import requests
import logging
from typing import Dict, List, Optional
import time
import os

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini LLM Service - GoI Google Gemini API"""

    def __init__(self, api_key: str = None, model: str = None, timeout: int = 120):
        """
        Khoi tao Gemini Service

        Args:
            api_key: Google API Key
            model: Model name (default from settings or gemini-1.5-flash)
            timeout: Thoi gian cho (giay)
        """
        from app.config import settings
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        if not self.api_key:
            logger.warning("Khong tim thay GOOGLE_API_KEY!")
        
        logger.info(f"[Gemini] Service khoi tao voi model: {self.model}")

    def _build_url(self, endpoint: str = "generateContent") -> str:
        """Build Gemini API URL"""
        return f"{self.base_url}/{self.model}:{endpoint}?key={self.api_key}"

    def query(self, messages: List[Dict], max_tokens: int = 2048, temperature: float = 0.7, json_mode: bool = False) -> Dict:
        """
        Gui query den Gemini API

        Args:
            messages: Danh sach tin nhan (OpenAI format)
            max_tokens: So token toi da
            temperature: Nhiet do sinh
            json_mode: Neu True, yeu cau output JSON

        Returns:
            {success, answer, error, latency, method}
        """
        logger.info(f"[Gemini] Query (model: {self.model}, max_tokens: {max_tokens})")
        
        start_time = time.time()
        
        if not self.api_key:
            return self._fallback_response(messages, start_time, "API key missing")
        
        # Chuyen doi messages sang Gemini format
        contents = self._convert_messages_to_contents(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            }
        }
        
        if json_mode:
            payload["generationConfig"]["response_mime_type"] = "application/json"
        
        try:
            url = self._build_url("generateContent")
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = self._extract_answer(data)
                
                logger.info(f"[Gemini] Thanh cong ({latency:.2f}s)")
                
                return {
                    "success": True,
                    "answer": answer,
                    "error": None,
                    "latency": latency,
                    "method": "gemini"
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"[Gemini] Loi: {error_msg}")
                
                return {
                    "success": False,
                    "answer": f"Loi API: {response.status_code}",
                    "error": error_msg,
                    "latency": latency,
                    "method": "gemini"
                }
                
        except requests.exceptions.Timeout:
            latency = time.time() - start_time
            logger.error(f"[Gemini] Timeout ({self.timeout}s)")
            
            return {
                "success": False,
                "answer": "Gemini Timeout - qua tre",
                "error": "timeout",
                "latency": latency,
                "method": "gemini"
            }
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[Gemini] Exception: {str(e)}")
            
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": latency,
                "method": "gemini"
            }

    def _convert_messages_to_contents(self, messages: List[Dict]) -> List[Dict]:
        """
        Chuyen doi OpenAI format sang Gemini format
        
        OpenAI format:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        
        Gemini format:
        [{"role": "model/user", "parts": [{"text": "..."}]}]
        """
        contents = []
        system_instruction = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction += content + "\n\n"
                continue
            
            # Map OpenAI role sang Gemini
            gemini_role = "user"
            if role == "model" or role == "assistant":
                gemini_role = "model"
            
            # Neu co system instruction, prepend vao tin nhan user dau tien
            if system_instruction and gemini_role == "user":
                content = system_instruction + content
                system_instruction = "" # Reset de chi prepend mot lan
            
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        
        # Neu chi co system instruction ma khong co user message
        if system_instruction and not contents:
            contents.append({
                "role": "user",
                "parts": [{"text": system_instruction}]
            })
            
        return contents


    def _extract_answer(self, data: Dict) -> str:
        """Trích xuất câu trả lời từ Gemini response"""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return "Khong co candidates"
                
            candidate = candidates[0]
            finish_reason = candidate.get("finishReason")
            if finish_reason and finish_reason != "STOP":
                logger.warning(f"[Gemini] Warning: finishReason is {finish_reason}")
                
            parts = candidate.get("content", {}).get("parts", [])
            if parts:
                # Ghep tat ca cac part lai neu co nhieu part
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                return "".join(text_parts)
            
            return "Khong co text trong response"
            
        except Exception as e:
            logger.error(f"Loi trich xuat answer: {e}")
            return f"Loi trich xuat: {str(e)}"

    def _fallback_response(self, messages: List[Dict], start_time: float, reason: str) -> Dict:
        """Fallback khi khong goi duoc API"""
        latency = time.time() - start_time
        
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")[:100]
                break
        
        fallback = f"""
[GEMINI FALLBACK MODE]

Khong the goi Gemini API: {reason}

Ly do: {reason}

De su dung Gemini:
1. Lay API key tu https://aistudio.google.com
2. Them vao .env: GOOGLE_API_KEY=your_key
3. Restart backend

---
Tin nhan cua ban: {user_message}...
"""
        
        logger.warning(f"[Gemini] Su dung fallback: {reason}")
        
        return {
            "success": False,
            "answer": fallback,
            "error": reason,
            "latency": latency,
            "method": "gemini_fallback"
        }

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
        """
        Transcribe audio to Vietnamese text using Gemini multimodal API.
        
        Args:
            audio_bytes: Raw audio bytes
            mime_type: MIME type (audio/webm, audio/mp3, audio/wav, etc.)
        
        Returns:
            {success, transcript, error, latency}
        """
        import base64
        import time

        logger.info(f"[Gemini STT] Transcribing {len(audio_bytes):,} bytes ({mime_type})")
        start_time = time.time()

        if not self.api_key:
            return {"success": False, "transcript": "", "error": "GOOGLE_API_KEY not set"}

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {"text": (
                        "Hãy transcribe chính xác toàn bộ nội dung âm thanh tiếng Việt sau đây. "
                        "Chỉ trả về văn bản transcription, không giải thích thêm."
                    )},
                    {"inline_data": {"mime_type": mime_type, "data": audio_b64}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 4096
            }
        }

        try:
            # Use self.model
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            response = requests.post(url, json=payload, timeout=120)
            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                transcript = self._extract_answer(data).strip()
                logger.info(f"[Gemini STT] OK ({latency:.1f}s): {transcript[:80]}")
                return {"success": True, "transcript": transcript, "error": None, "latency": latency}
            else:
                err = f"HTTP {response.status_code}: {response.text[:300]}"
                logger.error(f"[Gemini STT] {err}")
                return {"success": False, "transcript": "", "error": err, "latency": latency}

        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[Gemini STT] Exception: {e}")
            return {"success": False, "transcript": "", "error": str(e), "latency": latency}

    def extract_medical_info_from_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm", medical_record: str = "") -> dict:
        """
        Unify STT and Information Extraction in a single multimodal call.
        Faster, more accurate, and more robust.
        """
        import base64
        import time
        import re
        import json

        logger.info(f"[Gemini Full] Processing {len(audio_bytes):,} bytes ({mime_type})")
        start_time = time.time()

        if not self.api_key:
            return {"success": False, "transcript": "", "data": {}, "error": "GOOGLE_API_KEY not set"}

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        medical_record_text = f"Hồ sơ bệnh án cũ: {medical_record}" if medical_record else "Không có hồ sơ cũ."

        prompt = f"""Bạn là hệ thống trích xuất thông tin y khoa chuyên sâu trong lĩnh vực da liễu. 
Hãy lắng nghe âm thanh và thực hiện 2 nhiệm vụ:
1. Transcribe chính xác nội dung âm thanh tiếng Việt.
2. Trích xuất thông tin y khoa có cấu trúc từ nội dung đó (kết hợp với hồ sơ cũ: {medical_record_text}).

CẤU TRÚC JSON YÊU CẦU:
{{
  "transcript": "nội dung transcription tiếng Việt",
  "structured_data": {{
    "chief_complaint": "Lý do chính đi khám",
    "symptoms": ["triệu chứng 1", "triệu chứng 2"],
    "duration": "thời gian bị (ví dụ: 2 tuần)",
    "onset": "cách khởi phát và diễn tiến",
    "lesion_location": ["vị trí tổn thương 1", "vị trí 2"],
    "lesion_distribution": "cách phân bố tổn thương",
    "itching": true/false/null,
    "pain": true/false/null,
    "burning": true/false/null,
    "scaling": true/false/null,
    "blister": true/false/null,
    "discharge": true/false/null,
    "bleeding": true/false/null,
    "spreading_pattern": "hướng lan của tổn thương",
    "trigger_factors": ["yếu tố làm tăng triệu chứng"],
    "previous_treatment": ["các thuốc/cách đã điều trị trước đó"],
    "history_update": ["thông tin tiền sử mới ghi nhận"],
    "allergy_update": ["thông tin dị ứng mới"],
    "current_notes": "ghi chú khác của bác sĩ",
    "missing_required_fields": ["tên các trường bị thiếu thông tin"],
    "uncertain_fields": ["tên các trường có thông tin không rõ ràng"],
    "summary": "tóm tắt ngắn gọn tình trạng (1-2 câu)",
    "draft_notes": "ghi chú nháp cho bệnh án"
  }}
}}

**QUY TẮC:**
- TRẢ LỜI hoàn toàn bằng TIẾNG VIỆT.
- ĐẢM BẢO đầu ra là JSON hợp lệ. Không thêm bất kỳ giải thích nào bên ngoài JSON.
"""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": audio_b64}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
                "response_mime_type": "application/json"
            }
        }

        try:
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            response = requests.post(url, json=payload, timeout=120)
            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                answer = self._extract_answer(data)
                
                # Robust JSON extraction
                json_match = re.search(r'(\{[\s\S]*\})', answer)
                json_str = json_match.group(1).strip() if json_match else answer.strip()
                result_data = json.loads(json_str)
                
                transcript = result_data.get("transcript", "")
                structured = result_data.get("structured_data", {})
                
                # Frontend Compatibility Mapping
                structured["reason_for_visit"] = structured.get("reason_for_visit") or structured.get("chief_complaint", "")
                structured["main_symptoms"]    = structured.get("main_symptoms") or structured.get("symptoms", [])
                structured["onset_time"]       = structured.get("onset_time") or structured.get("duration") or structured.get("onset", "")
                structured["medical_history"]  = structured.get("medical_history") or structured.get("history_update", [])
                structured["related_factors"]  = structured.get("related_factors") or structured.get("trigger_factors", [])
                structured["missing_fields"]    = structured.get("missing_fields") or structured.get("missing_required_fields", [])
                
                if isinstance(structured.get("lesion_location"), list):
                    structured["lesion_location_str"] = ", ".join(structured["lesion_location"])
                
                logger.info(f"[Gemini Full] Thanh cong ({latency:.2f}s)")
                return {
                    "success": True,
                    "transcript": transcript,
                    "data": structured,
                    "error": None,
                    "latency": latency
                }
            else:
                err = f"HTTP {response.status_code}: {response.text[:300]}"
                logger.error(f"[Gemini Full] {err}")
                return {
                    "success": False,
                    "transcript": "",
                    "data": {},
                    "error": err,
                    "latency": latency
                }
                
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[Gemini Full] Exception: {str(e)}")
            return {
                "success": False,
                "transcript": "",
                "data": {},
                "error": str(e),
                "latency": latency
            }

    def test_connection(self) -> bool:
        """Test ket noi API"""
        result = self.query(
            [{"role": "user", "content": "Hello"}],
            max_tokens=50
        )
        return result.get("success", False)
