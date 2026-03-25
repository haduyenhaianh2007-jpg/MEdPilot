# MEDPILOT - Hướng Dẫn Hoàn Chỉnh

## 📁 Cấu Trúc Dự Án

```
C:\Dự án\Medplot\medpilot_remind\
│
├── app/                          # Backend FastAPI
│   ├── main.py                   # API endpoints chính
│   ├── config.py                 # Cấu hình từ .env
│   ├── schemas.py                # Request/Response models
│   ├── prompts.py                # System prompts cho LLM
│   ├── rag_engine.py              # ChromaDB RAG engine
│   └── service/
│       ├── vllm_service.py        # Gọi vLLM/Qwen API
│       ├── speech_extraction_service.py  # Speech + Extraction
│       ├── gemini_service.py      # Gemini API (deprecated)
│       └── claude_service.py      # Claude API (deprecated)
│
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── App.jsx               # Main app - routing theo role
│   │   ├── components/
│   │   │   └── RoleSelection.jsx  # Chọn Bác sĩ/Bệnh nhân
│   │   ├── pages/
│   │   │   ├── DoctorDashboard.jsx # Giao diện Bác sĩ
│   │   │   └── PatientChat.jsx     # Giao diện Bệnh nhân
│   │   ├── services/
│   │   │   └── api.js             # API calls
│   │   └── styles/
│   │       └── index.css          # Tailwind styles
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── notebook/                      # Google Colab Notebooks
│   ├── MedPilot_vLLM_Qwen_Colab.ipynb  # vLLM + Qwen cho RAG/Chat
│   └── MedPilot_PhoWhisper_Colab.ipynb # PhoWhisper + Extraction
│
├── database/
│   └── data/
│       └── diseases_data.json     # 219 diseases data
│
├── chroma_db/                     # ChromaDB vector store
│   └── ...                        # 75,659 chunks indexed
│
├── test/                          # Test files
├── .env                            # Environment variables
└── README.md
```

---

## 🔄 LUỒNG HOẠT ĐỘNG

### Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                          │
│    ┌─────────────────┐          ┌─────────────────┐             │
│    │ DoctorDashboard │          │  PatientChat   │             │
│    └────────┬────────┘          └────────┬────────┘             │
│             │                              │                     │
└─────────────┼──────────────────────────────┼─────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                          │
│                      localhost:3000                             │
│                      (Vite dev server)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                            │
│                   localhost:8000                                 │
│   ┌──────────────────────────────────────────────────────┐      │
│   │ /api/v1/query      - RAG Chat (Doctor/Patient)     │      │
│   │ /api/v1/chat       - Patient Chat                  │      │
│   │ /api/v1/speech/transcribe - Audio → Transcript      │      │
│   │ /api/v1/speech/extract    - Transcript → Structured │      │
│   └──────────────────────────────────────────────────────┘      │
│           │                        │                             │
│           ▼                        ▼                             │
│   ┌───────────────┐        ┌────────────────┐                   │
│   │  RAG Engine   │        │ LLM Service    │                   │
│   │  (ChromaDB)   │        │ (vLLM Service) │                   │
│   └───────────────┘        └────────┬───────┘                   │
│                                     │                           │
└─────────────────────────────────────┼───────────────────────────┘
                                      │ HTTPS
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COLAB (GPU Server)                          │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Colab 1: vLLM + Qwen2.5-1.5B                          │  │
│   │  Endpoint: /v1/chat/completions                         │  │
│   │  URL: https://xxx.ngrok-free.dev                        │  │
│   └─────────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Colab 2: PhoWhisper + vLLM Extraction                 │  │
│   │  Endpoints:                                             │  │
│   │    - /v1/audio/transcriptions (Whisper)                 │  │
│   │    - /v1/extract (Structured extraction)                │  │
│   │  URL: https://yyy.ngrok-free.dev                        │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 MÔ TẢ CHI TIẾT TỪNG FILE

### 1. BACKEND FILES

#### `app/main.py` (418+ lines)
**Mục đích**: FastAPI app - xử lý tất cả API endpoints

**Endpoints chính**:
| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/v1/ask-role` | GET | Hỏi user chọn role |
| `/api/v1/query` | POST | Query RAG (Doctor/Patient mode) |
| `/api/v1/chat` | POST | Patient chat liên tục |
| `/api/v1/speech/transcribe` | POST | Upload audio → Transcript |
| `/api/v1/speech/extract` | POST | Transcript → Structured info |

**Biến quan trọng**:
- `CONFIDENCE_THRESHOLD = 0.35` - Ngưỡng similarity cho RAG
- `conversation_history` - Lưu lịch sử chat

**Flow xử lý query**:
```
1. Retrieve RAG chunks (ChromaDB)
2. Check confidence threshold (similarity > 0.35?)
   - YES → Gọi vLLM → Trả response
   - NO → Trả "Chưa tìm thấy căn cứ phù hợp"
```

#### `app/config.py`
**Mục đích**: Đọc cấu hình từ `.env`

**Biến quan trọng**:
```python
VLLM_API_URL      # URL vLLM (Colab 1)
WHISPER_API_URL   # URL PhoWhisper (Colab 2)  
EXTRACTION_API_URL # URL Extraction (Colab 2)
```

#### `app/rag_engine.py` (253 lines)
**Mục đích**: Vector search với ChromaDB

**Class**: `RAGEngine`
- `load_diseases_from_json()` - Load diseases data
- `index_diseases()` - Index vào ChromaDB
- `retrieve(query, top_k)` - Tìm chunks liên quan, trả về:
  ```python
  {
    'disease': 'Tên bệnh',
    'content': 'Nội dung chunk',
    'distance': 0.3  # Cosine distance
  }
  ```

**Lưu ý**: Distance = 1 - similarity. Distance thấp = similarity cao

#### `app/prompts.py` (1000+ lines)
**Mục đích**: Tất cả system prompts cho LLM

**Prompts quan trọng**:

| Prompt | Mục đích |
|--------|-----------|
| `DOCTOR_MODE_SYSTEM_VI` | Prompt cho bác sĩ - dùng "CÓ THỂ" |
| `PATIENT_MODE_SYSTEM_VI` | Prompt cho bệnh nhân - cảnh báo an toàn |
| `NO_CONTEXT_DOCTOR_VI` | Response khi confidence thấp (Doctor) |
| `NO_CONTEXT_PATIENT_VI` | Response khi confidence thấp (Patient) |
| `RAG_CHAT_PROMPT_VI` | Prompt cho RAG chat |
| `PATIENT_RAG_CHAT_PROMPT_VI` | Prompt cho patient chat |

**Quy tắc quan trọng**:
- Doctor mode: LUÔN dùng "CÓ THỂ" khi gợi ý
- Patient mode: TUYỆT ĐỐI KHÔNG khuyên mua thuốc
- Low confidence: Trả về "Chưa tìm thấy căn cứ phù hợp"

#### `app/schemas.py`
**Mục đích**: Pydantic models cho request/response

**Models chính**:
```python
QueryRequest         # query, user_role, top_k, max_tokens, temperature
QueryResponse        # query, answer, retrieved_chunks, latency, success
ChatRequest          # message, conversation_id
SpeechExtractRequest # medical_record, include_transcript
StructuredMedicalInfo # reason_for_visit, main_symptoms, onset_time...
```

#### `app/service/vllm_service.py`
**Mục đích**: Gọi vLLM API (Colab)

**Method**:
```python
query(messages, max_tokens, temperature) -> {success, answer, error, latency}
```

---

### 2. FRONTEND FILES

#### `frontend/src/App.jsx`
**Mục đích**: Router theo user role

**Flow**:
```
User → RoleSelection → Doctor → DoctorDashboard
                       → Patient → PatientChat
```

#### `frontend/src/pages/DoctorDashboard.jsx` (~600 lines)
**Mục đích**: Giao diện bác sĩ

**Các bước (currentStep)**:
```
idle → recording → processing → reviewing
```

**State chính**:
```javascript
currentStep      // 'idle' | 'recording' | 'processing' | 'reviewing'
patientCode      // Mã bệnh nhân
audioFile        // File audio upload/record
transcript       // Text từ Whisper
extractedData    // Structured info từ AI
suggestions      // Gợi ý chẩn đoán, red flags...
```

**Flow xử lý audio**:
```
1. recordAudio() / uploadAudio() → audioFile
2. processAudio() → gọi /speech/transcribe
3. Transcript + Mock extraction → extractedData
4. Hiển thị form để sửa → saveConsultation()
```

**Các panel chính**:
- Transcript: Hiển thị text từ audio
- Form thông tin: reason_for_visit, symptoms, location...
- Gợi ý chẩn đoán: differential_diagnosis, red_flags
- Clinical reminders

#### `frontend/src/pages/PatientChat.jsx` (~324 lines)
**Mục đích**: Giao diện chatbot bệnh nhân

**State chính**:
```javascript
messages[]       // Lịch sử chat
input            // Text input
isRecording      // Đang ghi âm?
hasDangerKeywords // Có từ khóa nguy hiểm?
```

**Flow**:
```
1. User nhập câu hỏi / ghi âm
2. sendMessage() → /api/v1/query (user_role: 'patient')
3. Hiển thị response
4. Kiểm tra từ khóa nguy hiểm → show warning
```

**Safety Features**:
- Check từ khóa: "mua thuốc", "tự điều trị"...
- Hiển thị warning banner
- Luôn khuyến nghị khám bác sĩ

#### `frontend/src/services/api.js`
**Mục đích**: Centralized API calls

**Functions**:
```javascript
queryRAG(query, userRole)           // Query RAG
chatPatient(message, conversationId) // Patient chat
transcribeAudio(audioFile)            // Transcribe audio
extractMedicalInfo(transcript)        // Extract structured
```

---

### 3. COLAB NOTEBOOKS

#### `notebook/MedPilot_vLLM_Qwen_Colab.ipynb`
**Mục đích**: vLLM server cho RAG và Chat

**Chạy trên Port**: 8000 (ngrok → 8000)

**Models**:
- Qwen/Qwen2.5-1.5B-Instruct

**Endpoints exposed**:
```
GET  /              → Health check
GET  /health        → Status
POST /v1/chat/completions → OpenAI-compatible chat
```

**Setup flow**:
1. Install vLLM
2. Load model với vLLM
3. Start FastAPI server
4. Expose via ngrok
5. Copy URL → .env

#### `notebook/MedPilot_PhoWhisper_Colab.ipynb`
**Mục đích**: PhoWhisper + Extraction

**Chạy trên Ports**: 8001, 8002

**Models**:
- faster-whisper (medium) - Vietnamese ASR
- Qwen/Qwen2.5-1.5B-Instruct - Extraction

**Endpoints exposed**:
```
Port 8001:
  POST /v1/audio/transcriptions → Whisper API

Port 8002:
  POST /v1/extract → Extraction API
```

---

## 🔧 CẤU HÌNH .ENV

```env
# Paths
DISEASES_JSON=database/data/diseases_data.json
DB_PATH=chroma_db

# vLLM (Colab 1 - Chat/RAG)
VLLM_API_URL=https://xxx.ngrok-free.dev/v1/chat/completions
VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
LLM_TIMEOUT=120

# Whisper (Colab 2)
WHISPER_API_URL=https://yyy.ngrok-free.dev/v1/audio/transcriptions
EXTRACTION_API_URL=https://yyy.ngrok-free.dev/v1/extract

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# RAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TOP_K=3

# Confidence
CONFIDENCE_THRESHOLD=0.35  # Ngưỡng similarity
```

---

## 🚀 CÁCH KHỞI ĐỘNG

### 1. Khởi động Colab

**Colab 1 - vLLM + Qwen**:
```bash
1. Upload MedPilot_vLLM_Qwen_Colab.ipynb
2. Runtime → Factory reset runtime
3. Runtime → Run all
4. Copy URL → .env VLLM_API_URL
```

**Colab 2 - PhoWhisper**:
```bash
1. Upload MedPilot_PhoWhisper_Colab.ipynb
2. Runtime → Factory reset runtime
3. Runtime → Run all
4. Copy URLs → .env WHISPER_API_URL, EXTRACTION_API_URL
```

### 2. Khởi động Backend

```bash
cd C:\Dự án\Medplot\medpilot_remind
pip install -r requirements.txt  # Nếu cần
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Khởi động Frontend

```bash
cd C:\Dự án\Medplot\medpilot_remind\frontend
npm install  # Lần đầu
npm run dev
```

### 4. Truy cập

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

---

## ⚠️ VẤN ĐỀ CẦN GIẢI QUYẾT

### 1. Speech Extraction - CHƯA HOÀN THIỆN

**Vấn đề**: Hiện tại extraction dùng mock data, chưa gọi thật extraction API

**Cần làm**:
1. Gọi `/v1/extract` với transcript thật
2. Parse JSON response
3. Map vào form fields

**Code cần sửa trong `DoctorDashboard.jsx`**:
```javascript
// Thay vì mock, gọi API thật:
const processAudio = async () => {
  // ... transcribe ...
  
  // Gọi extraction API
  const extractRes = await axios.post(`${API_BASE}/speech/extract`, {
    transcript: transcriptText,
    medical_record: medicalRecord
  }, { timeout: 300000 })
  
  // Parse và map dữ liệu
  const extracted = JSON.parse(extractRes.data.extraction)
  setExtractedData(extracted)
}
```

### 2. Model Không Hỗ Trợ Image

**Vấn đề**: Qwen2.5-1.5B không hỗ trợ vision/image input

**Giải pháp**:
- Đã thêm validation chỉ chấp nhận audio files
- Hoặc nâng cấp lên Qwen2.5-VL (vision capable)

### 3. Timeout Issues

**Vấn đề**: Colab có thể bị ngắt, gây timeout

**Giải pháp**:
- Giữ Colab tab luôn mở
- Dùng Colab Pro để session lâu hơn
- Hoặc deploy lên cloud server

### 4. Conversation History

**Vấn đề**: Chat patient mode chưa dùng conversation_id để track history

**Cần làm**: Lưu history ở backend hoặc frontend

### 5. Error Handling

**Cần cải thiện**:
- Hiển thị toast/notification thay vì alert()
- Retry logic khi API fail
- Loading states chi tiết hơn

---

## 📋 CHECKLIST CÔNG VIỆC

### Cần hoàn thành:

- [ ] Kết nối extraction API thật vào DoctorDashboard
- [ ] Test đầy đủ flow: Record → Transcript → Extract → Display
- [ ] Thêm loading states
- [ ] Thêm error boundaries
- [ ] Test trên mobile
- [ ] Deploy lên production (nếu cần)

### Tối ưu thêm:

- [ ] Thêm authentication/authorization
- [ ] Lưu consultation history vào database
- [ ] Export PDF/Word consultation notes
- [ ] Multi-language support (English)

---

## 📞 LIÊN HỆ

- Backend API: http://localhost:8000/docs
- Colab 1: vLLM + Qwen
- Colab 2: PhoWhisper + Extraction

---

**Last Updated**: March 2026
