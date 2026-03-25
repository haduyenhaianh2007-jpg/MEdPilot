"""
Định nghĩa cấu trúc dữ liệu request/response
Đã dọn dẹp: loại bỏ schema trùng lặp, thêm validation
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal, Dict
from datetime import datetime


# ============ REQUEST MODELS ============

class QueryRequest(BaseModel):
    """Request query RAG - cho cả Doctor và Patient mode"""
    query: str  # Câu hỏi
    user_role: Optional[Literal["doctor", "patient"]] = None  # Chỉ chấp nhận 2 giá trị
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("query không được để trống")
        return v.strip()


class ChatRequest(BaseModel):
    """Request chat liên tục cho bệnh nhân"""
    message: str  # Câu hỏi mới nhất từ user
    conversation_id: Optional[str] = None  # ID để track conversation
    top_k: Optional[int] = 3  # Số kết quả retrieve

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("message không được để trống")
        return v.strip()


# ============ RESPONSE MODELS ============

class QueryResponse(BaseModel):
    """Response từ query RAG"""
    query: str
    answer: str
    retrieved_chunks: int
    latency: float
    success: bool


class ChatResponse(BaseModel):
    """Response chat từ AI (Patient mode)"""
    message: str  # Response từ AI
    is_dermatology: bool  # True = về da liễu, False = ngoài lĩnh vực
    has_medication_warning: bool = False  # True = phát hiện ý định mua thuốc
    conversation_id: str  # ID conversation
    retrieved_chunks: int  # Số chunks retrieve được
    latency: float  # Thời gian xử lý
    success: bool  # Success or not


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


# ============ SPEECH EXTRACTION MODELS ============

class SpeechExtractRequest(BaseModel):
    """Request trích xuất thông tin từ transcript"""
    transcript: str = ""              # Văn bản từ STT (bắt buộc để extract)
    medical_record: Optional[str] = ""  # Hồ sơ bệnh án cũ (text)
    include_transcript: bool = True  # Trả về transcript không


class StructuredMedicalInfo(BaseModel):
    """Thông tin y khoa có cấu trúc - Phiên bản 3 lớp (hỗ trợ cả cũ và mới)"""
    # --- New granular fields (3-layer design) ---
    chief_complaint: Optional[str] = ""
    symptoms: List[str] = []
    duration: Optional[str] = ""
    onset: Optional[str] = ""
    lesion_location: List[str] = []
    lesion_distribution: Optional[str] = ""
    itching: Optional[bool] = None
    pain: Optional[bool] = None
    burning: Optional[bool] = None
    scaling: Optional[bool] = None
    blister: Optional[bool] = None
    discharge: Optional[bool] = None
    bleeding: Optional[bool] = None
    spreading_pattern: Optional[str] = ""
    trigger_factors: List[str] = []
    previous_treatment: List[str] = []
    history_update: List[str] = []
    allergy_update: List[str] = []
    current_notes: Optional[str] = ""
    missing_required_fields: List[str] = []
    uncertain_fields: List[str] = []
    
    # --- Clinical Suggestions (Rule-based & AI hybrid) ---
    possible_considerations: List[str] = []
    alert_level: str = "normal"  # normal, warning, critical
    red_flags: List[str] = []
    questions_to_ask: List[str] = []
    clinical_reminders: List[str] = []
    
    # --- Frontend compatibility fields (Legacy mapping) ---
    reason_for_visit: Optional[str] = ""
    main_symptoms: List[str] = []
    onset_time: Optional[str] = ""
    medical_history: List[str] = []
    related_factors: List[str] = []
    missing_fields: List[str] = []
    
    # Common fields
    summary: Optional[str] = ""
    draft_notes: Optional[str] = ""
    source: Optional[Dict] = {}


class SpeechExtractResponse(BaseModel):
    """Response trích xuất từ audio"""
    transcript: str  # Văn bản từ audio
    structured_data: StructuredMedicalInfo  # Thông tin có cấu trúc
    success: bool
    error: Optional[str] = None


# ============ RETRIEVAL MODELS ============

class RetrievedChunk(BaseModel):
    """Một đoạn context được truy xuất"""
    disease: str                    # Tên bệnh
    content: str                    # Nội dung chunk
    similarity: float               # Điểm tương đồng (0-1)
    distance: float                 # Khoảng cách cosine
    rank: int                       # Thứ tự (1, 2, 3...)


class RetrieveRequest(BaseModel):
    """Request truy xuất context"""
    query: str                      # Câu hỏi
    top_k: Optional[int] = 5        # Số chunks lấy về
    min_similarity: Optional[float] = 0.0  # Ngưỡng similarity tối thiểu


class RetrieveResponse(BaseModel):
    """Response truy xuất context"""
    query: str                      # Câu hỏi đã truy xuất
    total_chunks: int              # Tổng số chunks tìm được
    chunks: List[RetrievedChunk]    # Danh sách chunks
    filtered_chunks: int           # Số chunks sau khi lọc theo threshold
    avg_similarity: float          # Similarity trung bình
    max_similarity: float          # Similarity cao nhất
    min_similarity_threshold: float  # Ngưỡng đã dùng
    success: bool
    latency: float
    message: Optional[str] = None