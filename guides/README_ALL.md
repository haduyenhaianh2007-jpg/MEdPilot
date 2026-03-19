# Hướng dẫn sử dụng MedPilot

## 1. Dành cho Users
- Đăng nhập hệ thống, chọn vai trò (bác sĩ hoặc bệnh nhân).
- Gửi câu hỏi về da liễu qua giao diện chat.
- Nhận phản hồi AI, cảnh báo thuốc nếu có.
- Lưu ý: Chỉ hỏi về lĩnh vực da liễu để nhận tư vấn chính xác.

## 2. Dành cho Backend Developers
- Đọc BACKEND_REFACTOR_SPEC.md để biết luồng xử lý chuẩn.
- Đảm bảo endpoint, schema, logging, error handling đúng spec.
- Tích hợp AI backend (Ollama/vLLM), tối ưu memory.
- Xử lý lỗi 422, validate payload, trả về lỗi rõ ràng.

## 3. Dành cho Frontend Developers
- Đọc BACKEND_API_GUIDE.md để biết cách gọi API.
- Gửi đúng payload, nhận đúng response từ backend.
- Tích hợp giao diện chat, cảnh báo thuốc, tracking conversation.
- Test các trường hợp edge case (empty, whitespace, out-of-scope).

## 4. Dành cho AI Supporters
- Đọc AI_ISSUES.md để biết các vấn đề tồn đọng AI.
- Bổ sung intent detection đa ngữ, prompt song ngữ.
- Tối ưu memory cho vLLM quantized, hướng dẫn cho user Windows.
- Bổ sung logging chi tiết, test coverage đủ.

---
Mọi thắc mắc, xem README.md, BACKEND_REFACTOR_SPEC.md, BACKEND_API_GUIDE.md, AI_ISSUES.md hoặc liên hệ dev chính.
