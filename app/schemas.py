"""
Định nghĩa cấu trúc dữ liệu request/response
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


# ============ REQUEST MODELS ============
class Message(BaseModel):
    """Một tin nhắn trong chat"""
    role: str  # "user" hoặc "assistant"
    content: str  # Nội dung tin nhắn


class QueryRequest(BaseModel):
    """Request query RAG - Generic"""
    query: str  # Câu hỏi
    user_role: Optional[str] = None  # "doctor" (bác sĩ) or "patient" (bệnh nhân)
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class DoctorQueryRequest(BaseModel):
    """Request cho chế độ BÁC SĨ - Upload file JSON"""
    # Nội dung JSON của bệnh nhân (parsed from file)
    clinical_info: Dict  # Thông tin lâm sàng từ file JSON
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    chief_complaint: Optional[str] = None
    top_k: Optional[int] = 5  # Số bệnh retrieve
    max_tokens: Optional[int] = 2000  # Chi tiết hơn cho bác sĩ
    temperature: Optional[float] = 0.5  # Ít random hơn để accuracy cao


# ============ RESPONSE MODELS ============
class QueryResponse(BaseModel):
    """Response từ query RAG - Generic"""
    query: str
    answer: str
    retrieved_chunks: int
    latency: float
    success: bool


class DoctorQueryResponse(BaseModel):
    """Response cho chế độ BÁC SĨ"""
    patient_name: Optional[str] = None
    chief_complaint: str
    # Gợi ý chẩn đoán chính
    primary_diagnosis: str
    # Chẩn đoán phản biện (differential diagnosis)
    differential_diagnosis: List[str]
    # Đề xuất xét nghiệm
    recommended_tests: List[str]
    # Ghi chú thêm
    clinical_notes: str
    # Tất cả dữ liệu retrieve
    retrieved_diseases: List[Dict]
    latency: float
    success: bool


class PatientChatResponse(BaseModel):
    """Response chat cho bệnh nhân"""
    message: str  # Response từ AI
    is_dermatology: bool  # True = về da liễu
    has_medication_warning: bool  # True = phát hiện mua thuốc
    conversation_id: str
    retrieved_chunks: int
    latency: float
    success: bool


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    model: str
    chat_api: str
    vector_db: str


class StatsResponse(BaseModel):
    """Statistics response"""
    total_chunks: int
    db_path: str
    chat_api: str
    model: str
    timestamp: datetime


class RoleSelectionResponse(BaseModel):
    """Response để hỏi user role"""
    message: str
    options: list  # ["doctor", "patient"]
    timestamp: datetime


class ReloadResponse(BaseModel):
    """Reload response"""
    status: str
    message: str
    diseases_loaded: int
    chunks_indexed: int
    timestamp: datetime


# ============ CHAT MODELS (Patient Mode) ============
class ChatMessage(BaseModel):
    """Một tin nhắn trong chat conversation"""
    role: str  # "user" hoặc "assistant"
    content: str  # Nội dung tin nhắn


class ChatRequest(BaseModel):
    """Request chat liên tục cho bệnh nhân"""
    message: str  # Câu hỏi mới nhất từ user
    conversation_id: Optional[str] = None  # ID để track conversation
    top_k: Optional[int] = 3  # Số kết quả retrieve


class ChatResponse(BaseModel):
    """Response chat từ AI"""
    message: str  # Response từ AI
    is_dermatology: bool  # True = về da liễu, False = ngoài lĩnh vực
    conversation_id: str  # ID conversation
    retrieved_chunks: int  # Số chunks retrieve được (nếu about dermatology)
    latency: float  # Thời gian xử lý
    success: bool  # Success or not