# Backend Refactor Spec - MedPilot

## 1. Mục tiêu
- Đảm bảo backend hoàn toàn tương thích với luồng AI và frontend.
- Chuẩn hóa schema, endpoint, logging, error handling.

## 2. Luồng xử lý chuẩn
### a. Role Selection
- GET /api/v1/ask-role
- Trả về: { "message": "...", "options": ["doctor", "patient"] }

### b. Doctor Mode
- POST /api/v1/query?role=doctor
- Nhận: { "query": "...", "top_k": 5 }
- Trả về: { "answer": "...", "retrieved_chunks": 5, "latency": 8.2 }

### c. Patient Mode (Single Query)
- POST /api/v1/query?role=patient
- Nhận: { "message": "..." }
- Trả về: { "answer": "...", "is_dermatology": true, "latency": 4.1 }

### d. Patient Mode (Chat)
- POST /api/v1/chat
- Nhận: { "message": "...", "conversation_id": "uuid", "top_k": 3 }
- Trả về: { "message": "...", "is_dermatology": true, "conversation_id": "uuid", "retrieved_chunks": 3, "latency": 2.5, "success": true }

## 3. Yêu cầu refactor
- Đảm bảo tất cả endpoint nhận đúng payload, trả đúng schema.
- Xử lý lỗi 422: validate payload, trả về lỗi rõ ràng nếu sai schema.
- Logging chi tiết: ghi lại request, response, lỗi, thời gian xử lý.
- Tối ưu memory cho AI backend (Ollama/vLLM).
- Tích hợp prompt song ngữ, tracking conversation.
- Đảm bảo frontend chỉ cần gửi đúng payload, nhận đúng response.

## 4. Đề xuất cấu trúc file
- app/main.py: định nghĩa endpoint, luồng xử lý.
- app/schemas.py: định nghĩa schema chuẩn.
- app/llm_service.py: tích hợp AI backend.
- app/config.py: cấu hình.
- logs/log_config.json: cấu hình log.
- test/test_interactive.py: test API.

## 5. Checklist cho backend dev
- [ ] Endpoint đúng spec
- [ ] Schema đúng chuẩn
- [ ] Logging chi tiết
- [ ] Error handling rõ ràng
- [ ] Tối ưu memory AI
- [ ] Prompt song ngữ
- [ ] Test coverage đủ

## 6. Hướng dẫn tích hợp frontend
- Frontend chỉ cần gửi đúng payload, nhận đúng response.
- Xem BACKEND_API_GUIDE.md để biết chi tiết.

---
Mọi thay đổi cần bám sát spec này để đảm bảo AI và frontend hoạt động ổn định, dễ mở rộng.
