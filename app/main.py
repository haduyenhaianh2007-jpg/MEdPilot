# -*- coding: utf-8 -*-
"""

API backend - RAG + vLLM (Colab)

Su dung vLLM API tren Colab

"""



from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form

from fastapi.middleware.cors import CORSMiddleware

import logging

from datetime import datetime

import time



from app.config import settings

from app.schemas import (

    QueryRequest, QueryResponse,

    RoleSelectionResponse, ChatRequest, ChatResponse,

    SpeechExtractRequest, SpeechExtractResponse, StructuredMedicalInfo,

    RetrieveRequest, RetrieveResponse, RetrievedChunk

)

from app.rag_engine import RAGEngine

from app.service.gemini_service import GeminiService

from app import prompts

import uuid
import os



logging.basicConfig(

    level=settings.LOG_LEVEL,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)

logger = logging.getLogger(__name__)



# Confidence threshold for RAG retrieval
# similarity = 1 - distance (cosine distance)
# If max similarity < threshold -> low confidence -> return "no context found"
CONFIDENCE_THRESHOLD = 0.20  # Lowered from 0.35 to improve suggestion visibility



app = FastAPI(

    title="MedPilot RAG Backend",

    description="RAG + Gemini",

    version="6.0"

)



app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



logger.info("Khoi tao services...\n")



# RAG Engine

rag_engine = RAGEngine(

    diseases_json=settings.DISEASES_JSON,

    db_path=settings.DB_PATH,

    embedding_model=settings.EMBEDDING_MODEL,

    top_k=settings.TOP_K,

    cache_size=settings.MODEL_CACHE_SIZE

)



# Load diseases

logger.info("Loading diseases from JSON...")

diseases = rag_engine.load_diseases_from_json()

if diseases:

    logger.info(f"Found {len(diseases)} diseases - will index on first query")

else:

    logger.warning("No diseases loaded!")



# Gemini Service
llm_service = GeminiService(
    api_key=settings.GOOGLE_API_KEY,
    model=settings.GEMINI_MODEL,
    timeout=settings.LLM_TIMEOUT
)



logger.info(f"Gemini Model: {llm_service.model}")
logger.info("Backend ready!\n")



# Conversation history - gioi han dung luong

MAX_HISTORY_PER_CONV = 10

conversation_history = {}



def get_conversation_history(conv_id: str, max_messages: int = MAX_HISTORY_PER_CONV) -> list:

    """Lay lich su hoi thoai, gioi han so tin nhan"""

    if conv_id not in conversation_history:

        return []

    history = conversation_history[conv_id]

    return history[-max_messages:] if len(history) > max_messages else history



def add_to_history(conv_id: str, role: str, content: str):

    """Them tin nhan vao lich su"""

    if conv_id not in conversation_history:

        conversation_history[conv_id] = []

    

    conversation_history[conv_id].append({"role": role, "content": content})

    

    # Gioi han kich thuoc

    if len(conversation_history[conv_id]) > MAX_HISTORY_PER_CONV * 2:

        conversation_history[conv_id] = conversation_history[conv_id][-MAX_HISTORY_PER_CONV*2:]



def is_dermatology_question(user_message: str) -> bool:

    """

    Kiểm tra câu hỏi của người dùng có thuộc phạm vi da liễu hay không.

    Dùng so khớp theo từ khóa.

    """

    # Danh sách từ khóa cho chủ đề da liễu

    derm_keywords = [

        "da", "mun", "noi do", "ngua", "kho", "cham", "gau", "nam", 

        "veu", "mun rop", "mun coc", "seo", "chan nam", "lang ben",

        "viem da", "di ung da", "ton thuong da", "benh da", "skin",

        "rash", "acne", "eczema", "psoriasis", "fungal", "dermatitis",

        "hoi nach", "mo hoi", "nam da", "bach bien", "benh ly da",

        "mong", "toc", "duong am", "my pham", "chong nang", "sun",

        "che do cham soc", "lam sach", "rua mat", "mat na",

        "ben", "hang", "co", "la", "mun dung"

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





@app.post("/api/v1/retrieve", response_model=RetrieveResponse)

async def retrieve_context(req: RetrieveRequest):

    """

    🔍 Retrieve Context Endpoint - Trả thẳng các đoạn context liên quan

    

    Không qua LLM - chỉ trả về chunks từ Vector DB

    

    Args:

        query: Câu hỏi truy xuất

        top_k: Số chunks lấy về (mặc định 5)

        min_similarity: Ngưỡng similarity tối thiểu (mặc định 0.0)

    

    Returns:

        - Danh sách chunks với metadata (disease, content, similarity)

        - Thông tin về nguồn tài liệu

    """

    from app.schemas import RetrievedChunk

    

    logger.info(f"\n{'='*60}")

    logger.info(f"🔍 RETRIEVE CONTEXT: {req.query[:80]}...")

    logger.info(f"{'='*60}")

    

    start_time = time.time()

    

    try:

        # Retrieve from ChromaDB

        top_k = req.top_k or 5

        retrieved = rag_engine.retrieve(req.query, top_k=top_k)

        

        logger.info(f"✅ Retrieved {len(retrieved)} chunks from ChromaDB")

        

        # Build chunks with metadata

        chunks = []

        total_similarity = 0.0

        max_similarity = 0.0

        

        for idx, r in enumerate(retrieved, 1):

            distance = r.get('distance', 1.0)

            similarity = round(1 - distance, 4)  # Convert distance to similarity

            

            chunk = RetrievedChunk(

                disease=r.get('disease', 'Unknown'),

                content=r.get('content', ''),

                similarity=similarity,

                distance=round(distance, 4),

                rank=idx

            )

            chunks.append(chunk)

            

            total_similarity += similarity

            if similarity > max_similarity:

                max_similarity = similarity

        

        # Calculate average similarity

        avg_similarity = round(total_similarity / len(chunks), 4) if chunks else 0.0

        

        # Filter chunks by min_similarity if specified

        min_sim = req.min_similarity or 0.0

        filtered_chunks = [c for c in chunks if c.similarity >= min_sim]

        

        logger.info(f"📊 Similarity - Max: {max_similarity:.4f}, Avg: {avg_similarity:.4f}")

        logger.info(f"📊 Filtered: {len(filtered_chunks)}/{len(chunks)} chunks (threshold: {min_sim})")

        

        latency = time.time() - start_time

        

        return RetrieveResponse(

            query=req.query,

            total_chunks=len(retrieved),

            chunks=chunks,

            filtered_chunks=len(filtered_chunks),

            avg_similarity=avg_similarity,

            max_similarity=max_similarity,

            min_similarity_threshold=min_sim,

            success=True,

            latency=latency

        )

        

    except Exception as e:

        error_msg = f"Retrieve Error: {type(e).__name__} - {str(e)}"

        logger.error(f"Error: {error_msg}")

        import traceback

        logger.error(traceback.format_exc())

        raise HTTPException(status_code=500, detail=error_msg)





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



        # Step 1.5: Check confidence threshold

        if retrieved:

            max_distance = retrieved[0].get('distance', 1.0)

            similarity = 1 - max_distance

            logger.info(f"📊 Max similarity: {similarity:.3f} (threshold: {CONFIDENCE_THRESHOLD})")

            

            if similarity < CONFIDENCE_THRESHOLD:

                logger.info(f"⛔ LOW CONFIDENCE - Similarity {similarity:.3f} < {CONFIDENCE_THRESHOLD}")

                

                if user_role == "doctor":

                    no_context_prompt = prompts.NO_CONTEXT_DOCTOR_VI.format(user_message=req.query)

                else:

                    no_context_prompt = prompts.NO_CONTEXT_PATIENT_VI.format(user_message=req.query)

                

                latency = time.time() - start_time

                return QueryResponse(

                    query=req.query,

                    answer=no_context_prompt,

                    retrieved_chunks=len(retrieved),

                    latency=latency,

                    success=True,

                    confidence=similarity

                )



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



        logger.info(f"Done ({latency:.2f}s)")



        return QueryResponse(

            query=req.query,

            answer=result.get("answer", "Xin loi, khong tao duoc response."),

            retrieved_chunks=len(retrieved),

            latency=latency,

            success=result.get("success", False)

        )



    except Exception as e:

        error_msg = f"Query Error: {type(e).__name__} - {str(e)}"

        logger.error(f"Error: {error_msg}")

        import traceback

        logger.error(traceback.format_exc())

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

        

        # Luon goi RAG de tim context - KHONG dung keyword check

        # is_derm = is_dermatology_question(req.message)  # Bo keyword check

        

        # Lay context tu RAG

        retrieved = rag_engine.retrieve(req.message, top_k=req.top_k or 3)

        is_derm = len(retrieved) > 0

        

        logger.info(f"🔍 Retrieved: {len(retrieved)} chunks")

        

        # Neu khong tim thay context

        if not is_derm:

            logger.info(f"⛔ Khong tim thay thong tin trong CSDL")

            

            response_text = """Xin lỗi, tôi không tìm thấy thông tin về câu hỏi của bạn trong cơ sở dữ liệu.



Vui lòng hỏi về các chủ đề liên quan đến da liễu như:

- Các bệnh da (mụn, chàm, nấm, viêm da,...)

- Chăm sóc da (dưỡng ẩm, chống nắng,...)

- Triệu chứng da liễu"""

            

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

            add_to_history(conv_id, "user", req.message)

            add_to_history(conv_id, "assistant", response_text)

            

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

        add_to_history(conv_id, "user", req.message)

        

        # Prepare messages for LLM (include conversation history)

        messages = [

            {"role": "system", "content": full_system_message}

        ]

        

        # Add conversation history (keep last 10 messages to save tokens)

        for m in get_conversation_history(conv_id, max_messages=10):

            messages.append(m)

        

        # Query LLM

        logger.info(f"🤖 Generating response...")

        result = llm_service.query(messages, max_tokens=settings.MAX_TOKENS)

        

        response_text = result.get("answer", "Xin lỗi, không thể tạo response.")

        

        # Add response to history

        add_to_history(conv_id, "assistant", response_text)

        

        latency = time.time() - start_time

        

        logger.info(f"Done ({latency:.2f}s)")

        

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

        logger.error(f"Error: {error_msg}")

        import traceback

        logger.error(traceback.format_exc())

        raise HTTPException(status_code=500, detail=error_msg)





# ============ SPEECH EXTRACTION ENDPOINTS ============



@app.post("/api/v1/speech/extract", response_model=SpeechExtractResponse)
async def speech_extract(req: SpeechExtractRequest):
    """
    🧠 Speech Extraction Endpoint
    Nhận transcript → Gemini trích xuất thông tin y khoa có cấu trúc
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🧠 SPEECH EXTRACTION REQUEST")
    logger.info(f"📝 Transcript length: {len(req.transcript)} chars")
    logger.info(f"{'='*60}")

    start_time = time.time()

    if not req.transcript or not req.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript không được để trống")

    try:
        from app.service.speech_extraction_service import SpeechExtractionService
        speech_service = SpeechExtractionService()
        
        extract_result = speech_service.extract_structured_info(
            transcript=req.transcript,
            medical_record=req.medical_record or ""
        )
        
        latency = time.time() - start_time
        
        if extract_result.get("success"):
            data = extract_result.get("data", {})
            
            # Ensure all required fields for StructuredMedicalInfo are present
            # Use **data to ensure all granular fields are passed to the model
            # while still handling legacy fields correctly.
            structured = StructuredMedicalInfo(**data)
            
            logger.info(f"✅ Extracted via Gemini in {latency:.2f}s")
            return SpeechExtractResponse(transcript=req.transcript, structured_data=structured, success=True)
        else:
            logger.error(f"❌ Extraction failed: {extract_result.get('error')}")
            raise HTTPException(status_code=500, detail=extract_result.get("error", "Extraction failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal extraction error: {str(e)}")




@app.post("/api/v1/speech/process-full", response_model=SpeechExtractResponse)
async def process_full_audio(
    file: UploadFile = File(...),
    medical_record: Optional[str] = Form("")
):
    """
    🚀 Unified Audio Processing Endpoint
    Audio → Gemini Multimodal → {Transcript + Structured Medical Data}
    Single stage for maximum speed and accuracy.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 FULL PROCESS: {file.filename}")
    logger.info(f"{'='*60}")

    start_time = time.time()
    audio_bytes = await file.read()
    content_type = file.content_type or "audio/webm"
    audio_format = content_type.split("/")[-1] if "/" in content_type else "webm"

    try:
        from app.service.speech_extraction_service import SpeechExtractionService
        speech_service = SpeechExtractionService()
        
        result = speech_service.process_audio_full(
            audio_data=audio_bytes,
            format=audio_format,
            medical_record=medical_record
        )
        
        latency = time.time() - start_time
        
        if result.get("success"):
            data = result.get("structured_data", {})
            
            # Build structured object
            # Use **data to ensure all granular fields are passed to the model
            # while still handling legacy fields correctly.
            data["source"] = {"engine": "gemini-2.5-flash-unified", "latency": latency}
            structured = StructuredMedicalInfo(**data)
            
            logger.info(f"✅ Full processing successful in {latency:.2f}s")
            return SpeechExtractResponse(
                transcript=result.get("transcript", ""),
                structured_data=structured,
                success=True
            )
        else:
            logger.error(f"❌ Full processing failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Full processing failed"))

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Full processing error: {e}")
        
        # Log to debug file too
        with open(r"c:\Dự án\Medplot\medpilot_remind\logs\debug_extraction.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.ctime()} EXCEPTION ---\n")
            f.write(error_trace)
            
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")


@app.post("/api/v1/speech/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    🎙️ Transcribe audio — Gemini (Primary) → Wav2Vec2 → PhoWhisper fallback
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🎙️ TRANSCRIBE: {file.filename}")
    logger.info(f"{'='*60}")

    start_time = time.time()
    audio_bytes = await file.read()
    content_type = file.content_type or "audio/webm"
    
    # ── 1. Gemini STT (Primary) ───────────────────────────────
    if settings.GOOGLE_API_KEY:
        try:
            result = llm_service.transcribe_audio(audio_bytes, mime_type=content_type)
            if result.get("success"):
                latency = time.time() - start_time
                logger.info(f"✅ Gemini STT OK ({latency:.1f}s)")
                return {"transcript": result["transcript"], "language": "vi",
                        "latency": latency, "success": True, "engine": "gemini"}
            logger.warning(f"[Gemini STT] {result.get('error')} — trying Wav2Vec2")
        except Exception as e:
            logger.warning(f"[Gemini STT] Exception: {e} — trying Wav2Vec2")

    # ── 2. Wav2Vec2 Vietnamese (Local) ──────────────────────
    try:
        from app.service import wav2vec2_service
        result = wav2vec2_service.transcribe(audio_bytes, mime_type=content_type)
        if result.get("success"):
            latency = time.time() - start_time
            logger.info(f"✅ Wav2Vec2 OK ({latency:.1f}s)")
            return {"transcript": result["transcript"], "language": "vi",
                    "latency": latency, "success": True, "engine": "wav2vec2"}
        logger.warning(f"[Wav2Vec2] {result.get('error')} — trying PhoWhisper")
    except Exception as e:
        logger.warning(f"[Wav2Vec2] Exception: {e} — trying PhoWhisper")

    # ── 3. PhoWhisper (Colab) last resort ───────────────────
    if settings.WHISPER_API_URL:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                files = {"file": (file.filename or "audio.webm", audio_bytes, content_type)}
                data = {"model": "base", "language": "vi", "task": "transcribe"}
                response = await client.post(
                    settings.WHISPER_API_URL,
                    files=files,
                    data=data,
                    timeout=120,
                    headers={"ngrok-skip-browser-warning": "true", "User-Agent": "MedPilot-Backend/1.0"}
                )
            
            latency = time.time() - start_time
            if response.status_code == 200:
                result = response.json()
                transcript = result.get("text", "")
                logger.info(f"✅ PhoWhisper OK ({latency:.1f}s): {transcript[:80]}")
                return {
                    "transcript": transcript,
                    "language": result.get("language", "vi"),
                    "latency": latency,
                    "success": True,
                    "engine": "phowhisper"
                }
            else:
                logger.error(f"[PhoWhisper] error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.error(f"[PhoWhisper] Exception: {e}")

    # Final fallback
    raise HTTPException(status_code=500, detail="Transcription failed after all attempts.")





