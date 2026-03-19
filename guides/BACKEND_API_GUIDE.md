# Backend API Guide - MedPilot

## 1. Tổng quan
- Backend sử dụng FastAPI, cung cấp các endpoint phục vụ AI tư vấn da liễu.
- Người làm backend chỉ cần đảm bảo các endpoint đúng spec, trả về đúng schema.

## 2. Các endpoint chính
### a. Role Selection
- GET /api/v1/ask-role
- Response: { "message": "...", "options": ["doctor", "patient"] }

### b. Doctor Mode
- POST /api/v1/query?role=doctor
- Body: { "query": "patient symptoms", "top_k": 5 }
- Response: { "answer": "...", "retrieved_chunks": 5, "latency": 8.2 }

### c. Patient Mode (Single Query)
- POST /api/v1/query?role=patient
- Body: { "message": "dermatology question" }
- Response: { "answer": "...", "is_dermatology": true, "latency": 4.1 }

### d. Patient Mode (Chat)
- POST /api/v1/chat
- Body: { "message": "question", "conversation_id": "uuid", "top_k": 3 }
- Response: { "message": "...", "is_dermatology": true, "conversation_id": "uuid", "retrieved_chunks": 3, "latency": 2.5, "success": true }

## 3. Cách gọi API
- Dùng requests (Python), curl, hoặc Postman.
- Đảm bảo Content-Type: application/json.
- Gửi đúng payload theo schema từng endpoint.

### Ví dụ Python:
```python
import requests
payload = {
    "message": "Mụn trứng cá là gì?",
    "conversation_id": "debug_001",
    "top_k": 3
}
response = requests.post("http://localhost:8000/api/v1/chat", json=payload)
print(response.status_code, response.text)
```

### Ví dụ curl:
```sh
curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message":"Mụn trứng cá là gì?","conversation_id":"debug_001","top_k":3}'
```

## 4. Lưu ý
- Đảm bảo backend trả về đúng schema, không thừa/thiếu trường.
- Nếu lỗi 422, kiểm tra lại payload và endpoint.
- Logging chi tiết để debug nhanh.

## 5. Spec chi tiết
- Xem README.md và AI_ISSUES.md để biết thêm về kiến trúc, vấn đề tồn đọng, và hướng fix.
