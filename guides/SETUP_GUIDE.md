# MedPilot Setup Guide

## 1. Chuẩn bị môi trường
- Python >= 3.10 (khuyến nghị 3.14)
- Git, pip, venv
- (Tùy chọn) WSL2/Ubuntu nếu dùng vLLM quantized

## 2. Clone dự án
```sh
git clone <repo-url>
cd medpilot_remind
```

## 3. Tạo và kích hoạt venv
```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

## 4. Cài đặt dependencies
```sh
pip install -r requirements.txt
```

## 5. Cấu hình .env
- Copy .env.example thành .env
- Chỉnh sửa các biến: OLLAMA_URL, CHAT_API_URL, DB_PATH, MODEL...

## 6. Chạy backend
```sh
python -m uvicorn app.main:app --port 8000 --reload --log-config logs/log_config.json
```

## 7. Chạy test
```sh
python tests/test_interactive.py
python tests/test_e2e.py
```

## 8. Chạy AI backend (Ollama/vLLM)
- Ollama: `ollama serve`
- vLLM: Xem hướng dẫn vLLM, khuyến nghị WSL2/Ubuntu

## 9. Gửi request thử nghiệm
- Dùng Postman, curl, hoặc script Python
- Đảm bảo payload đúng schema từng endpoint

## 10. Debug lỗi
- Xem logs/log_config.json, server.log, test_error_log.txt
- Dùng collect_error_info.py để lấy log lỗi và request thực tế

---
Mọi thắc mắc, xem README.md hoặc liên hệ dev chính.
