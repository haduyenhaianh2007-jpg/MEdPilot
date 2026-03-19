# MedPilot AI Backend & Frontend Guide

## 1. Tổng quan dự án
- Dự án MedPilot: Hệ thống AI hỗ trợ tư vấn da liễu, phân vai Bác sĩ/Patient, tích hợp RAG, LLM (Ollama/vLLM), cảnh báo thuốc, tracking conversation.
- Kiến trúc: Backend FastAPI, Frontend (tùy chọn), Chat Server (Ollama/vLLM), Vector DB, Prompt bilingual.

## 2. Hướng dẫn Backend
### a. Cài đặt
- Python >= 3.10 (khuyến nghị 3.14)
- Tạo venv: `python -m venv .venv`
- Kích hoạt venv: `./.venv/Scripts/activate` (Windows) hoặc `source .venv/bin/activate` (Linux)
- Cài dependencies: `pip install -r requirements.txt`

### b. Chạy Backend
- Chạy server: `python -m uvicorn app.main:app --port 8000 --reload --log-config logs/log_config.json`
- Đảm bảo file .env đã cấu hình đúng (OLLAMA_URL, CHAT_API_URL, DB_PATH, MODEL...)

### c. Test API
- Gửi request đúng schema (xem ví dụ ở Spec).
- Chạy test: `python test/test_interactive.py`

## 3. Hướng dẫn Frontend
- Frontend có thể là web app, Postman, hoặc script Python/curl.
- Đảm bảo gửi request đúng schema cho từng endpoint.
- Đọc README.md để biết các endpoint và payload.

## 4. Kiến trúc AI
- LLM Backend: Ollama/vLLM (OpenAI compatible)
- Vector DB: ChromaDB
- Prompt: song ngữ, tối ưu cho từng vai trò
- RAG: retrieve context, sinh response
- Cảnh báo thuốc: detect intent, sinh cảnh báo
- Tracking conversation: lưu history, sinh response liên tục

## 5. Spec dự án
### a. Endpoints
- GET /api/v1/ask-role: chọn vai trò
- POST /api/v1/query?role=doctor: truy vấn chuyên sâu
- POST /api/v1/query?role=patient: truy vấn thông thường
- POST /api/v1/chat: chat liên tục (patient)

### b. Schema
- ChatRequest: {"message": str, "conversation_id": str, "top_k": int}
- QueryRequest: {"query": str, "user_role": str, ...}

### c. Model
- Ollama: qwen2.5, llama2, mistral...
- vLLM: quantized model, OpenAI API

## 6. Vấn đề tồn đọng AI

## 7. File cấu trúc gọn
guides/COMPLETE_TEST_GUIDE.md: hướng dẫn chi tiết test
guides/TEST_REFERENCE.md: reference API

---
Mọi thắc mắc, xem README.md hoặc liên hệ dev chính.
