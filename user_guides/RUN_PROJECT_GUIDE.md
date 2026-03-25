# HƯỚNG DẪN CHẠY DỰ ÁN MEDPILOT

## 1. Chuẩn bị môi trường
- Cài Python >= 3.10 (khuyến nghị 3.14)
- Cài pip, venv
- Clone repo về máy

## 2. Tạo và kích hoạt virtual environment
```powershell
cd "c:\Dự án\Medplot\medpilot_remind"
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

## 4. Cấu hình file .env
- Copy .env.example thành .env
- Chỉnh sửa các biến: LLM_API_URL, VLLM_MODEL, DB_PATH, EMBEDDING_MODEL...

## 5. Khởi động Ollama/vLLM backend
- Ollama: `ollama serve` (giữ terminal chạy)
- vLLM: Xem hướng dẫn trong guides/README_ALL.md

## 6. Khởi động backend FastAPI
```powershell
python -m uvicorn app.main:app --port 8000 --reload --log-config logs/log_config.json
```

## 7. Chạy test tự động
```powershell
python test/test_e2e.py
```

## 8. Chạy test tương tác
```powershell
python test/test_interactive.py
```

## 9. Kiểm tra log
- Xem logs/backend.log, logs/request.log, logs/server.log để debug

## 10. Troubleshooting
- Nếu lỗi 422: Kiểm tra schema request/response, file app/schemas.py
- Nếu lỗi import: Kiểm tra requirements.txt, venv
- Nếu backend không chạy: Kiểm tra .env, log, port

## 11. Tài liệu bổ sung
- Xem guides/README_ALL.md, guides/COMPLETE_TEST_GUIDE.md, guides/FINAL_CHECKLIST.md
- Xem user_guides/README.md để biết thêm hướng dẫn chi tiết

---
**Mọi thắc mắc vui lòng liên hệ nhóm phát triển hoặc xem thêm tài liệu trong các folder guides, user_guides, backend_guides, frontend_guides, ai_support_guides.**
