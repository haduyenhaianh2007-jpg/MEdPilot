# MedPilot AI Backend & Frontend Guide

## 1. Project Structure (Cleaned)

- .env / .env.example: Environment variables
- collect_error_info.py: Script to collect backend logs & request
- COMPLETE_TEST_GUIDE.md: Full test guide
- ollama.log: Ollama server log
- OPTIMIZATION_GUIDE.md: AI optimization tips
- OPTIMIZATION_TIER_2.5_FINAL.md: Final optimization tier
- QUICK_START.md: Quick start instructions
- requirements.txt: Python dependencies
- run_tests.py: Test runner
- server.log: Backend log
- test_error_log.txt: Test error log
- TEST_REFERENCE.md: Test reference

## 2. Usage Guide

### Backend
1. Cài Python >= 3.10, pip, venv
2. Tạo venv và cài dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Chạy backend:
   ```
   python -m uvicorn app.main:app --port 8000 --reload --log-config logs/log_config.json
   ```
4. Đảm bảo .env đã cấu hình đúng model, API URL, DB_PATH, ...

### Frontend
- Đảm bảo backend đã chạy ở port 8000
- Gửi request đúng schema (xem Spec bên dưới)
- Nếu dùng Postman/curl, gửi đúng payload cho endpoint

## 3. AI Architecture & Model
- LLM Backend: Ollama/vLLM (OpenAI compatible)
- Model: Qwen2.5, GPTQ/AWQ quantized (tối ưu RAM)
- Vector DB: ChromaDB
- RAG Engine: Retrieve medical context, feed to LLM
- Role-based: Doctor/Patient mode, medication warning, scope checking

## 4. API Spec

### /api/v1/chat (Patient Chat)
- Method: POST
- Payload:
  ```json
  {
    "message": "Câu hỏi của user",
    "conversation_id": "uuid (tùy chọn)",
    "top_k": 3
  }
  ```
- Response:
  ```json
  {
    "message": "AI trả lời",
    "is_dermatology": true,
    "has_medication_warning": false,
    "conversation_id": "uuid",
    "retrieved_chunks": 3,
    "latency": 1.23,
    "success": true
  }
  ```

### /api/v1/query (Doctor/Patient Single Query)
- Method: POST
- Payload: QueryRequest/DoctorQueryRequest

### /api/v1/ask-role
- Method: GET
- Response: { "message": "...", "options": ["doctor", "patient"] }

## 5. Outstanding AI Issues
- Lỗi 422 khi payload không đúng schema (đã hướng dẫn fix)
- Chưa có kiểm tra input tiếng Việt/Anh tự động
- Chưa có kiểm tra model tải đúng (Ollama/vLLM)
- Chưa có hướng dẫn chi tiết cho vLLM quantized trên WSL2
- Chưa có script tự động kiểm tra health các backend
- Chưa có test coverage cho edge cases (empty, whitespace, medication intent)

## 6. Spec for Future Devs
- Đảm bảo mọi request gửi đúng schema
- Kiểm tra log backend khi gặp lỗi
- Cập nhật .env cho đúng model/backend
- Thêm test cho các trường hợp đặc biệt
- Tối ưu RAM khi dùng quantized model
- Bổ sung hướng dẫn cho frontend tích hợp AI

---
Nếu cần chi tiết về từng phần, xem các file hướng dẫn và test trong repo. Mọi vấn đề AI còn tồn đọng đã liệt kê ở mục 5 để người sau fix tiếp.