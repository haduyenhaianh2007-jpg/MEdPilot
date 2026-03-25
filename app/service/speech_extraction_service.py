# -*- coding: utf-8 -*-
"""
Speech-to-Text + Information Extraction Service
STT: Google Gemini multimodal API
Extract: Google Gemini LLM
"""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SpeechExtractionService:
    """Service for speech-to-text and medical information extraction via Gemini"""

    def __init__(self, api_url: str = None, whisper_api_url: str = None):
        """
        Backward-compatible constructor – extra args are ignored.
        API key is read from GOOGLE_API_KEY env var (loaded via .env).
        """
        import os
        self._api_key = os.getenv("GOOGLE_API_KEY", "")
        logger.info("[SpeechExtraction] Service initialized (Gemini backend)")

    # ------------------------------------------------------------------
    # Internal helper – lazy import GeminiService
    # ------------------------------------------------------------------
    def _gemini(self):
        from app.service.gemini_service import GeminiService
        return GeminiService(api_key=self._api_key)

    # ------------------------------------------------------------------
    # STT
    # ------------------------------------------------------------------
    def transcribe_audio(self, audio_data: bytes, format: str = "webm") -> Dict:
        """
        Transcribe audio using Gemini multimodal API.

        Returns:
            {success, text, error}
        """
        mime_type = f"audio/{format}"
        result = self._gemini().transcribe_audio(audio_data, mime_type=mime_type)
        return {
            "success": result.get("success", False),
            "text": result.get("transcript", ""),
            "error": result.get("error"),
        }

    # ------------------------------------------------------------------
    # Structured extract
    # ------------------------------------------------------------------
    def _normalize_transcript(self, transcript: str) -> str:
        """
        Giai đoạn 1: Chuẩn hóa transcript
        - Bỏ từ đệm, khoảng trắng thừa
        - Sửa lỗi STT phổ biến
        """
        import re
        if not transcript:
            return ""
            
        # Basic cleaning
        lines = transcript.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove filler words (basic Vietnamese fillers)
            for filler in ["ạ", "dạ", "ừm", "ờ", "thì", "là", "mà"]:
                line = re.sub(rf'\b{filler}\b', '', line, flags=re.IGNORECASE)
            cleaned_lines.append(line.strip())
            
        return "\n".join(cleaned_lines)

    def extract_structured_info(self, transcript: str, medical_record: str = "") -> Dict:
        """
        Giai đoạn 2 & 3: Extract structured info với schema và prompt tối ưu
        """
        if not transcript:
            return {"success": False, "data": {}, "error": "No transcript provided"}

        # 1. Normalization
        normalized_transcript = self._normalize_transcript(transcript)
        medical_record_text = medical_record if medical_record else "Không có hồ sơ cũ."

        # 2. Build Prompt (Giai đoạn 3: Structured Prompt)
        prompt = f"""Bạn là hệ thống trích xuất thông tin y khoa chuyên sâu trong lĩnh vực da liễu.

NHIỆM VỤ:
- Đọc transcript hội thoại bác sĩ – bệnh nhân và hồ sơ cũ (nếu có).
- Trích xuất thông tin vào đúng các field đã cho.
- KHÔNG suy diễn quá mức.
- Nếu không đủ dữ kiện cho một field, điền null (với boolean) hoặc chuỗi rỗng/mảng rỗng.
- Nếu dữ kiện mơ hồ hoặc mâu thuẫn, thêm tên field đó vào `uncertain_fields`.
- Nếu thiếu dữ liệu quan trọng (ví dụ: vị trí, thời gian bị), thêm vào `missing_required_fields`.
- CHỈ trả về JSON hợp lệ.

DỮ LIỆU ĐẦU VÀO:
- Hồ sơ cũ: {medical_record_text}
- Transcript: 
{normalized_transcript}

CẤU TRÚC JSON YÊU CẦU:
{{
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
"""

        messages = [
            {"role": "system", "content": "You are a professional medical data extractor. Output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ]

        result = self._gemini().query(messages, max_tokens=4096, temperature=0.1, json_mode=True)

        if not result.get("success"):
            return {"success": False, "data": {}, "error": result.get("error")}

        content = result.get("answer", "")

        # 3. Robust JSON extraction & Validation
        import re
        try:
            json_match = re.search(r'(\{[\s\S]*\})', content)
            json_str = json_match.group(1).strip() if json_match else content.strip()
            structured = json.loads(json_str)
            
            # Default values for missing keys to ensure schema compliance
            expected_keys = [
                "chief_complaint", "symptoms", "duration", "onset", 
                "lesion_location", "lesion_distribution", "itching", "pain", 
                "burning", "scaling", "blister", "discharge", "bleeding", 
                "spreading_pattern", "trigger_factors", "previous_treatment", 
                "history_update", "allergy_update", "current_notes", 
                "missing_required_fields", "uncertain_fields", "summary", "draft_notes"
            ]
            
            # 4. Frontend Compatibility Mapping
            structured["reason_for_visit"] = structured.get("reason_for_visit") or structured.get("chief_complaint", "")
            structured["main_symptoms"]    = structured.get("main_symptoms") or structured.get("symptoms", [])
            structured["onset_time"]       = structured.get("onset_time") or structured.get("duration") or structured.get("onset", "")
            structured["medical_history"]  = structured.get("medical_history") or structured.get("history_update", [])
            structured["related_factors"]  = structured.get("related_factors") or structured.get("trigger_factors", [])
            structured["missing_fields"]    = structured.get("missing_fields") or structured.get("missing_required_fields", [])
            
            # Ensure lesion_location is a list but frontend might expect string for some displays
            # though the form uses it as a string input. Let's provide a joined string if it's a list.
            if isinstance(structured.get("lesion_location"), list):
                # For input fields, string is better
                structured["lesion_location_str"] = ", ".join(structured["lesion_location"])
            
            # 5. Apply Clinical Rule-Based Logic (NEW)
            structured = self._apply_clinical_logic(structured)
            
            return {"success": True, "data": structured, "error": None}
            
        except Exception as e:
            logger.error(f"[Extraction] Refactored JSON error: {e}. Raw: {content[:200]}")
            return {
                "success": True, 
                "data": {
                    "summary": "Không thể phân tích dữ liệu cấu trúc",
                    "draft_notes": content
                }, 
                "error": f"JSON parse error: {str(e)}"
            }

    def _apply_clinical_logic(self, data: dict) -> dict:
        """
        Apply heuristic rules for suggestions, red flags, and questions.
        This provides reliable feedback without relying solely on RAG.
        """
        import re
        
        # Initialize containers if missing
        data["possible_considerations"] = data.get("possible_considerations") or []
        data["red_flags"] = data.get("red_flags") or []
        data["questions_to_ask"] = data.get("questions_to_ask") or []
        data["clinical_reminders"] = data.get("clinical_reminders") or []
        data["alert_level"] = "normal"

        # 1. DIAGNOSIS LOGIC (Possible Considerations)
        reason = (data.get("reason_for_visit") or "").lower()
        trigger = ", ".join(data.get("related_factors") or []).lower()
        location = ", ".join(data.get("lesion_location") or []).lower()
        history = ", ".join(data.get("medical_history") or []).lower()
        
        # Rule: Hand + Detergent -> Contact Dermatitis
        if ("bàn tay" in location or "ngón tay" in location) and ("nước rửa chén" in trigger or "xà phòng" in trigger or "hóa chất" in trigger):
            data["possible_considerations"].append("Cân nhắc viêm da tiếp xúc kích ứng (irritant contact dermatitis)")
        
        # Rule: History of Atopic Dermatitis -> Flare-up
        if "viêm da cơ địa" in history or "atopy" in history or "chàm" in history:
            data["possible_considerations"].append("Cân nhắc đợt bùng phát viêm da cơ địa (atopic dermatitis flare-up)")

        # 2. RED FLAGS LOGIC
        symptoms_str = ", ".join(data.get("main_symptoms") or []).lower()
        onset_str = (data.get("onset_time") or "").lower()
        
        # Checklist for Red Flags
        if "sốt" in symptoms_str or "mệt" in symptoms_str:
            data["red_flags"].append("Có dấu hiệu sốt/mệt mỏi: Cần loại trừ nhiễm trùng toàn thân")
            data["alert_level"] = "warning"
            
        if "lan nhanh" in onset_str or "lan rộng" in onset_str:
            data["red_flags"].append("Tổn thương lan rộng nhanh: Cần theo dõi sát")
            data["alert_level"] = "warning"
            
        if "chảy dịch" in symptoms_str or "mủ" in symptoms_str:
            data["red_flags"].append("Có chảy dịch/mủ: Nguy cơ bội nhiễm vi khuẩn")
            data["alert_level"] = "warning"

        if data["alert_level"] == "warning" and len(data["red_flags"]) >= 2:
            data["alert_level"] = "critical"

        # 3. QUESTIONS TO ASK (Dynamic)
        # Rule: trigger vague
        if not data.get("related_factors") or "không rõ" in trigger:
            data["questions_to_ask"].append("Bệnh nhân có tiếp xúc với hóa chất, mỹ phẩm hay dị nguyên nào mới không?")
            
        # Rule: treatment vague
        prev_treat = ", ".join(data.get("previous_treatment") or []).lower()
        if not data.get("previous_treatment") or "không rõ" in prev_treat:
            data["questions_to_ask"].append("Bệnh nhân đã bôi/uống thuốc gì cụ thể? Có còn nhớ tên thuốc hay mang theo vỏ thuốc không?")
            
        # Rule: missing burning/pain sense
        if data.get("burning") is None:
            data["questions_to_ask"].append("Bệnh nhân có cảm giác rát hoặc nóng da tại vùng tổn thương không?")
            
        if not data.get("medical_history"):
            data["questions_to_ask"].append("Bệnh nhân có tiền sử dị ứng thuốc, thức ăn hay các bệnh lý nền khác không?")

        return data


    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def process_audio_full(self, audio_data: bytes, format: str = "webm", medical_record: str = "") -> Dict:
        """
        Unified Full Pipeline: Audio → Gemini → {Transcript + Structured Data}
        Uses a single multimodal call for speed and accuracy.
        """
        logger.info("[SpeechExtraction] Processing audio via Unified Gemini Pipeline...")
        mime_type = f"audio/{format}"
        
        result = self._gemini().extract_medical_info_from_audio(
            audio_bytes=audio_data, 
            mime_type=mime_type, 
            medical_record=medical_record
        )

        if not result.get("success"):
            return {
                "success": False,
                "transcript": result.get("transcript", ""),
                "structured_data": {},
                "error": result.get("error"),
            }

        # Apply clinical rules
        structured_data = self._apply_clinical_logic(result.get("data", {}))

        return {
            "success": True,
            "transcript": result.get("transcript", ""),
            "structured_data": structured_data,
            "error": None,
        }
