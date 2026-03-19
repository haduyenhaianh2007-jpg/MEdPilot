"""
API backend - đã điều chỉnh cho dự án lớn.
⚡ Tối ưu bộ nhớ: nạp lười, cache, thu gom rác.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import time
import gc  # ⚡ Garbage collection

from app.config import settings
from app.schemas import (
    QueryRequest, QueryResponse, HealthResponse,
    StatsResponse, ReloadResponse, RoleSelectionResponse,
    ChatRequest, ChatResponse, DoctorQueryResponse
)
from app.rag_engine import RAGEngine
from app.llm_service import LLMService
from app import prompts
import uuid

# Cấu hình logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ KHỞI TẠO FASTAPI ============
app = FastAPI(
    title="MedPilot RAG Backend",
    description="Complete RAG + LLM System - Memory Optimized",
    version="1.0"
)

# CORS cho phép frontend hoặc công cụ khác gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ KHỞI TẠO DỊCH VỤ ============
logger.info("🚀 Initializing services...\n")

# ⚡ Bật cơ chế thu gom rác mạnh tay
gc.enable()
gc.set_threshold(settings.GC_INTERVAL or 1000)  # ⚡ Dọn rác mạnh tay
logger.info(f"🧹 Ngưỡng GC được đặt thành {settings.GC_INTERVAL or 1000} lần cấp phát")

# RAG Engine (bản JSON) - ⚡ Có nạp lười và cache
rag_engine = RAGEngine(
    diseases_json=settings.DISEASES_JSON,
    db_path=settings.DB_PATH,
    embedding_model=settings.EMBEDDING_MODEL,
    top_k=settings.TOP_K,
    cache_size=settings.MODEL_CACHE_SIZE  # ⚡ Cache embedding rất nhỏ
)

# Dịch vụ LLM (có chế độ dự phòng nếu backend chưa sẵn sàng)
llm_service = LLMService(
    api_url=settings.LLM_API_URL,
    model=settings.VLLM_MODEL,
    timeout=settings.TIMEOUT
)

# Nạp danh sách bệnh ngay khi khởi động
logger.info("📂 Loading diseases from JSON...")
diseases = rag_engine.load_diseases_from_json()

if diseases:
    logger.info(f"📊 Found {len(diseases)} diseases - will index on first query")
    # Không index ngay để tiết kiệm bộ nhớ, chỉ index khi cần
else:
    logger.warning("⚠️  No diseases loaded!")
    logger.warning("   Run: python convert_text_to_json.py")

logger.info("✅ Backend ready!\n")

# ============ TIỆN ÍCH ============
# Bộ đếm request để quản lý bộ nhớ
request_counter = {"count": 0}

def cleanup_request():
    """Dọn dẹp sau mỗi request."""
    request_counter["count"] += 1
    if request_counter["count"] % 5 == 0:  # Mỗi 5 request
        logger.debug(f"🧹 Dọn GC mạnh tay (request #{request_counter['count']})")
        gc.collect()
        gc.collect()  # Gọi thu gom hai lần cho sạch hơn

# Lịch sử hội thoại lưu trong bộ nhớ (demo; bản thật nên dùng database)
conversation_history = {}

def is_dermatology_question(user_message: str) -> bool:
    """
    Kiểm tra câu hỏi của người dùng có thuộc phạm vi da liễu hay không.
    Dùng so khớp theo từ khóa.
    """
    # Danh sách từ khóa cho chủ đề da liễu
    derm_keywords = [
        "da", "mụn", "nổi đỏ", "ngứa", "khô", "chàm", "gàu", "nấm", 
        "vêu", "mụn rộp", "mụn cóc", "sẹo", "chân nấm", "lang ben",
        "viêm da", "dị ứng da", "tổn thương da", "bệnh da", "skin",
        "rash", "acne", "eczema", "psoriasis", "fungal", "dermatitis",
        "hôi nách", "mồ hôi", "nám da", "bạch biến", "bệnh lý da",
        "móng", "tóc", "dưỡng ẩm", "mỹ phẩm", "chống nắng", "sun",
        "chế độ chăm sóc", "làm sạch", "rửa mặt", "mặt nạ"
    ]
    
    # Kiểm tra xem có từ khóa nào xuất hiện trong nội dung không
    message_lower = user_message.lower()
    for keyword in derm_keywords:
        if keyword in message_lower:
            return True
    
    # Nếu không khớp từ khóa nào thì coi là ngoài phạm vi
    return False


def check_medication_intent(user_message: str) -> bool:
    """
    Phát hiện người dùng có ý định mua thuốc mà chưa tham khảo bác sĩ hay không.
    """
    medication_keywords = [
        "mua thuốc", "mua kem", "mua dung dịch", "mua gel",
        "thuốc gì", "kem nào", "dung dịch nào", "gel nào",
        "bôi cái gì", "uống cái gì", "tiêm cái gì",
        "ở đâu mua", "bán ở đâu", "nhà thuốc", "hiệu thuốc",
        "liều lượng", "dùng bao nhiêu", "bôi bao nhiêu",
        "tự mua", "tự dùng", "tự bôi", "tự uống",
        "có được bán không", "bán không", "giá bao nhiêu"
    ]
    
    message_lower = user_message.lower()
    
    for keyword in medication_keywords:
        if keyword in message_lower:
            # Double check it's not just a question about medication in general
            # (e.g., "what is this medicine?")
            if any(x in message_lower for x in ["gì", "nào", "bao nhiêu", "ở đâu", "mua", "bôi", "uống", "dùng"]):
                return True
    
    return False

# ============ ENDPOINTS ============

@app.get("/api/v1/ask-role", response_model=RoleSelectionResponse)
async def ask_user_role():
    """🚀 Hỏi user là bác sĩ hay bệnh nhân - ENDPOINT ĐẦU TIÊN"""
    
    message = """👋 Xin chào! Chào mừng đến với MedPilot - Trợ lý AI Hỗ Trợ Chẩn Đoán Da Liễu

Để có thể giúp bạn tốt nhất, vui lòng cho biết bạn là:

**1️⃣ BÁC SĨ** - Tôi sẽ cung cấp gợi ý chẩn đoán chi tiết từ kho tri thức y tế
**2️⃣ BỆNH NHÂN** - Tôi sẽ trả lời Q&A thân thiện và hướng dẫn bạn tới bác sĩ

👉 Vui lòng gửi request tới /api/v1/query với {"query": "...", "user_role": "doctor"} hoặc {"user_role": "patient"}"""
    
    logger.info(f"📋 Role selection requested\n")
    
    return RoleSelectionResponse(
        message=message,
        options=["doctor", "patient"],
        timestamp=datetime.now()
    )

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest, role: str = Query(None)):
    """
    🩺 RAG Query Endpoint - Supports both doctor and patient modes
    
    Query parameters:
    - role=doctor → Doctor diagnostic mode (detailed, technical)
    - role=patient → Patient education mode (simple, no diagnosis)
    - If role not specified, defaults to patient (safer)
    """

    logger.info(f"\n{'='*60}")
    logger.info(f"❓ QUERY: {req.query[:80]}...")
    
    # Determine role - from request body or query param, default to patient
    user_role = (role or req.user_role or "patient").lower()
    
    if user_role not in ["doctor", "patient"]:
        raise HTTPException(status_code=400, detail='role must be "doctor" or "patient"')
    
    logger.info(f"👤 ROLE: {user_role.upper()}")
    logger.info(f"{'='*60}")

    start_time = time.time()

    try:
        # Step 1: Retrieve relevant diseases
        logger.info(f"🔍 Retrieving...")
        top_k = req.top_k or (5 if user_role == "doctor" else 3)
        retrieved = rag_engine.retrieve(req.query, top_k=top_k)

        logger.info(f"✅ Retrieved {len(retrieved)} chunks")

        # Step 2: Generate response based on role
        logger.info(f"🤖 Generating answer ({user_role} mode)...")

        # Build context from retrieved diseases
        context = "\n\n".join([f"[{r['disease']}] {r['content']}" for r in retrieved])

        # Select role-specific system prompt
        if user_role == "doctor":
            system_message = prompts.DOCTOR_MODE_SYSTEM_VI
            max_tokens = req.max_tokens or 2000
            temperature = req.temperature or 0.5  # Lower temp for accuracy
            logger.info(f"👨‍⚕️  Doctor Mode - Detailed diagnostic support")
        else:
            system_message = prompts.PATIENT_MODE_SYSTEM_VI
            max_tokens = req.max_tokens or 1000
            temperature = req.temperature or 0.7
            logger.info(f"🧑‍🤝‍🧑 Patient Mode - Educational Q&A")

        # Append retrieved context to system message
        full_system_message = f"""{system_message}

**KHO TRI THỨC Y TẾ:**
{context}"""

        # Build messages for LLM
        user_prompt = f"""Câu hỏi: {req.query}

Vui lòng trả lời HOÀN TOÀN bằng TIẾNG VIỆT."""

        messages = [
            {"role": "system", "content": full_system_message},
            {"role": "user", "content": user_prompt}
        ]

        # Step 3: Query LLM
        result = llm_service.query(messages, max_tokens=max_tokens)

        latency = time.time() - start_time

        logger.info(f"✅ Done ({latency:.2f}s)")
        
        # ⚡ Cleanup memory
        gc.collect()
        cleanup_request()

        return QueryResponse(
            query=req.query,
            answer=result.get("answer", "Xin lỗi, không thể tạo response."),
            retrieved_chunks=len(retrieved),
            latency=latency,
            success=result.get("success", False)
        )

    except Exception as e:
        error_msg = f"Query Error: {type(e).__name__} - {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        # ⚡ Cleanup even on error
        gc.collect()
        cleanup_request()
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/v1/chat", response_model=ChatResponse)
async def patient_chat(req: ChatRequest):
    """
    💬 Patient Chat Endpoint - Continuous Q&A about dermatology
    
    Features:
    - Continuous conversation history
    - Dermatology scope checking
    - Medication purchase warning detection
    - Educational content only (no diagnosis)
    """
    
    # Generate or use existing conversation ID
    conv_id = req.conversation_id if req.conversation_id else str(uuid.uuid4())
    
    logger.info(f"\n{'='*60}")
    logger.info(f"💬 CHAT: {req.message[:80]}...")
    logger.info(f"👤 CONVERSATION: {conv_id}")
    logger.info(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Initialize conversation if new
        if conv_id not in conversation_history:
            conversation_history[conv_id] = []
            logger.info(f"📝 Created new conversation")
        
        # Check if question is about dermatology
        is_derm = is_dermatology_question(req.message)
        
        logger.info(f"🔍 Question type: {'DERMATOLOGY' if is_derm else 'OUT OF SCOPE'}")
        
        # If out of scope, return polite refusal
        if not is_derm:
            logger.info(f"⛔ Question is outside dermatology scope")
            
            response_text = """Xin lỗi, tôi chỉ được đào tạo để trả lời các câu hỏi liên quan đến **da liễu**.

Câu hỏi của bạn ngoài lĩnh vực chuyên môn của tôi. 

Nếu bạn có bất kỳ câu hỏi nào về:
- 🔬 Các bệnh da (mụn, chàm, nấm, viêm da,...)
- 💆 Chăm sóc da (dưỡng ẩm, chống nắng, rửa mặt,...)
- 🏥 Phòng ngừa và làm đẹp

Tôi rất sẵn lòng giúp đỡ! Vui lòng hỏi lại về chủ đề liên quan đến da liễu."""
            
            latency = time.time() - start_time
            
            return ChatResponse(
                message=response_text,
                is_dermatology=False,
                has_medication_warning=False,
                conversation_id=conv_id,
                retrieved_chunks=0,
                latency=latency,
                success=True
            )
        
        # Check for medication purchase intent
        has_med_warning = check_medication_intent(req.message)
        
        if has_med_warning:
            logger.info(f"⚠️  Medication purchase intent detected!")
            
            response_text = """⚠️ **CẢNH BÁO QUAN TRỌNG** ⚠️

Bạn không nên **TỰ MUA** bất kỳ **LOẠI THUỐC NÀO** mà chưa tư vấn ý kiến bác sĩ da liễu!

**Vì sao điều này quan trọng:**
- 💊 Mỗi loại thuốc có tác dụng phụ khác nhau
- 👤 Tình trạng da của từng người khác nhau
- ⚠️ Liều lượng sai có thể gây nguy hiểm cho sức khỏe
- 🔬 Bác sĩ cần kiểm tra để chẩn đoán chính xác trước

**Bạn cần làm:**
1️⃣ **Đi khám bác sĩ da liễu** để được chẩn đoán chính xác
2️⃣ Bác sĩ sẽ **kê đơn** loại thuốc phù hợp với tình trạng của bạn
3️⃣ Mua **đúng loại** và **đúng liều** theo hướng dẫn của bác sĩ

🏥 **Vui lòng đặt lịch khám bác sĩ da liễu ngay hôm nay!**

---

Tôi vẫn sẵn lòng trả lời các câu hỏi khác về kiến thức da liễu."""
            
            latency = time.time() - start_time
            
            # Add to history
            conversation_history[conv_id].append({"role": "user", "content": req.message})
            conversation_history[conv_id].append({"role": "assistant", "content": response_text})
            
            return ChatResponse(
                message=response_text,
                is_dermatology=True,
                has_medication_warning=True,
                conversation_id=conv_id,
                retrieved_chunks=0,
                latency=latency,
                success=True
            )
        
        # If dermatology question (no med warning), retrieve context + generate response
        logger.info(f"📚 Retrieving medical context...")
        retrieved = rag_engine.retrieve(req.message, top_k=req.top_k or 3)
        
        logger.info(f"✅ Retrieved {len(retrieved)} chunks")
        
        # Build context
        context = "\n\n".join([f"[{r['disease']}] {r['content']}" for r in retrieved])
        
        # Build system message for patient chat
        system_message = prompts.PATIENT_MODE_SYSTEM_VI
        
        full_system_message = f"""{system_message}

**KHO TRI THỨC Y TẾ:**
{context}"""
        
        # Add to conversation history
        conversation_history[conv_id].append({
            "role": "user",
            "content": req.message
        })
        
        # Prepare messages for LLM (include conversation history)
        messages = [
            {"role": "system", "content": full_system_message}
        ]
        
        # Add conversation history (keep last 5 exchanges to save tokens)
        for m in conversation_history[conv_id][-10:]:
            messages.append(m)
        
        # Query LLM
        logger.info(f"🤖 Generating response...")
        result = llm_service.query(messages, max_tokens=settings.MAX_TOKENS)
        
        response_text = result.get("answer", "Xin lỗi, không thể tạo response.")
        
        # Add response to history
        conversation_history[conv_id].append({
            "role": "assistant",
            "content": response_text
        })
        
        latency = time.time() - start_time
        
        logger.info(f"✅ Done ({latency:.2f}s)")
        
        # ⚡ Cleanup memory
        gc.collect()
        cleanup_request()
        
        return ChatResponse(
            message=response_text,
            is_dermatology=True,
            has_medication_warning=False,
            conversation_id=conv_id,
            retrieved_chunks=len(retrieved),
            latency=latency,
            success=result.get("success", False)
        )
    
    except Exception as e:
        error_msg = f"Chat Error: {type(e).__name__} - {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        # ⚡ Cleanup even on error
        gc.collect()
        cleanup_request()
        raise HTTPException(status_code=500, detail=error_msg)