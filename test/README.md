# 🧪 Bộ Test MedPilot

## 📋 Các File Test

### 1. `test_doctor_mode.py` - Chế Độ Bác Sĩ
Kiểm tra chế độ cho bác sĩ:
- Một câu hỏi đơn lẻ (single query)
- Hội thoại nhiều lượt (multi-turn conversation)
- Giải thích: Bác sĩ có thể hỏi thêm để làm rõ chẩn đoán

**Chạy**: `python test/test_doctor_mode.py`

### 2. `test_patient_mode.py` - Chế Độ Bệnh Nhân
Kiểm tra chế độ cho bệnh nhân:
- Hỏi đáp Q&A về bệnh da liễu
- Phát hiện cảnh báo khi bệnh nhân định mua thuốc
- Từ chối câu hỏi ngoài phạm vi da liễu
- Theo dõi lịch sử hội thoại

**Chạy**: `python test/test_patient_mode.py`

### 3. `test_e2e.py` - Luồng End-to-End Hoàn Chỉnh
Kiểm tra toàn bộ luồng người dùng:
- Test lựa chọn vai trò (role selection endpoint)
- Test luồng bác sĩ hoàn chỉnh
- Test luồng bệnh nhân hoàn chỉnh
- Test độ bền của API

**Chạy**: `python test/test_e2e.py` (được khuyến nghị)

---

## 🚀 Cách Chạy Test

### Phương Pháp 1: Tự Động (Khuyến Nghị)

#### Windows:
```powershell
cd "c:\Dự án\Medplot\medpilot_remind"
powershell -ExecutionPolicy Bypass -File DEPLOY_WINDOWS_VI.ps1
```

#### Linux/Mac:
```bash
cd ~/MedPilot
chmod +x QUICKSTART_VI.sh
./QUICKSTART_VI.sh
```

### Phương Pháp 2: Thủ Công (3 Cửa Sổ Terminal)

#### Terminal 1: Khởi Động Ollama
```bash
ollama serve
# Chờ: 🦙 Ollama is running
```

#### Terminal 2: Khởi Động Backend
```bash
cd "c:\Dự án\Medplot\medpilot_remind"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# Chờ: Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 3: Chạy Test (Cửa Sổ Mới)
```bash
cd "c:\Dự án\Medplot\medpilot_remind"

# Chạy test end-to-end (bao quát)
python test/test_e2e.py

# HOẶC chạy test riêng lẻ:
python test/test_doctor_mode.py
python test/test_patient_mode.py
```

---

## ✅ Kết Quả Dự Kiến

### Chế Độ Bác Sĩ - PHẢI PASS
```
INPUT:  "Bệnh nhân bị nổi đỏ, ngứa 2 tuần, tay phải nặng hơn..."
OUTPUT: "Gợi ý chẩn đoán:
          1. Viêm da tiếp xúc (80%)
          2. Viêm da cơ địa (70%)
          3. Viêm da dị ứng (60%)
          
          Chi tiết: [RAG retrieved info]...
          Bác sĩ cần xét nghiệm..."
TIME:    5-8 giây
✅ PASS: Response chuyên sâu, chi tiết, có gợi ý
```

### Chế Độ Bệnh Nhân - PHẢI PASS

#### Test 1: Câu Hỏi Bình Thường
```
INPUT:  "Mụn trứng cá là bệnh gì?"
OUTPUT: "Mụn trứng cá là tình trạng xảy ra khi...
          [Giải thích đơn giản]
          
          Để chẩn đoán chính xác, vui lòng đi khám bác sĩ da liễu."
TIME:    3-5 giây
✅ PASS: Trả lời giáo dục, KHÔNG chẩn đoán
```

#### Test 2: Phát Hiện Mua Thuốc
```
INPUT:  "Tôi nên mua loại kem nào để trị mụn?"
OUTPUT: "⚠️ CẢNH BÁO QUAN TRỌNG
          
          Bạn không nên tự mua bất kỳ thuốc nào mà chưa tư vấn bác sĩ!
          
          Vui lòng đi khám bác sĩ da liễu để được tư vấn."
TIME:    2-3 giây
✅ PASS: Phát hiện cảnh báo, từ chối mua thuốc
```

#### Test 3: Ngoài Phạm Vi Da Liễu
```
INPUT:  "Tôi bị đau bụng, phải làm sao?"
OUTPUT: "Tôi chỉ chuyên về bệnh da liễu, không thể trả lời câu hỏi này.

          Vui lòng đi khám bác sĩ tổng quát để được hỗ trợ tốt hơn."
TIME:    2-3 giây
✅ PASS: Từ chối lịch sự, khuyên khám bác sĩ khác
```

#### Test 4: Lịch Sử Hội Thoại
```
USER 1:  "Eczema là gì?"
BOT:     "Eczema (viêm da) là..."
USER 2:  "Nó lây được không?"
BOT:     "Eczema không lây. Nó là tình trạng di truyền..."
         [Dùng context từ câu trước]
✅ PASS: Giữ ngữ cảnh, trả lời hợp lý
```

### Lựa Chọn Vai Trò - PHẢI PASS
```
REQUEST: GET /api/v1/ask-role
RESPONSE: {
  "message": "Xin chào! 👋 Chào mừng...",
  "options": ["doctor", "patient"],
  "timestamp": "2026-03-18..."
}
✅ PASS: Endpoint hoạt động, trả về hai tùy chọn
```

---

## 🐛 Khắc Phục Sự Cố

### Lỗi 1: "❌ API không phản hồi"
```bash
# Kiểm tra Backend có chạy không:
curl http://localhost:8000/api/v1/ask-role

# Kiểm tra port 8000 có chiếm không (Windows):
netstat -ano | findstr :8000

# Khắc phục: Giết process và khởi động lại
taskkill /PID <PID> /F
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Lỗi 2: "⏱️ Timeout"
```bash
# Kiểm tra Ollama:
ollama serve               # Kiểm tra dịch vụ
ollama list               # Kiểm tra model (xem qwen2.5:7b)

# Khắc phục: Khởi động lại Ollama
taskkill /IM ollama.exe /F
ollama serve
```

### Lỗi 3: "❌ Lỗi Retrieval"
```bash
# Kiểm tra file dữ liệu:
# - app/database/data/diseases_data.json (phải 6.49 MB)

# Nếu không có, khắc phục: Rebuild vector DB
rm -r chroma_db
# Test sẽ tự rebuild lại

# Kiểm tra model LLM:
ollama list | grep qwen2.5:7b
```

### Lỗi 4: "❌ ImportError"
```bash
# Cài lại phụ thuộc:
pip install -r requirements.txt --force-reinstall

# Hoặc cài lại từng package:
pip install fastapi pydantic requests chromadb sentence-transformers
```

---

## 📊 Mục Tiêu Hiệu Năng

| Chỉ Số | Mục Tiêu | Ghi Chú |
|--------|---------|---------|
| Doctor Query Response | < 15 giây | Khoá bệnh + LLM sinh text |
| Patient Query Response | < 10 giây | Nhanh hơn, less complex |
| Retrieval Accuracy | > 80% | Tùy vào từ khóa |
| Medication Warning Detection | 100% | Dựa vào keyword matching |
| Non-derm Rejection | 100% | Tự động từ chối |
| Conversation History | ✅ | Lưu trong session |

---

## 📝 Lưu Ý

- **Thời gian chạy test**: 2-3 phút cho end-to-end
- **Kích thước dữ liệu**: 219 bệnh (6.49 MB JSON)
- **Model LLM**: Qwen2.5:7b (nhanh hơn llama2)
- **Lưu trữ chat**: In-memory (có thể upgrade lên DB)

---

## 📞 Cần Hỗ Trợ?

1. Xem **FINAL_CHECKLIST_VI.md** - Danh sách kiểm tra chi tiết
2. Xem **IMPLEMENTATION_SUMMARY_VI.md** - Hướng dẫn kỹ thuật
3. Kiểm tra file log:
   - `server.log` - Lỗi backend
   - `ollama.log` - Lỗi Ollama

---

**Cập Nhật Lần Cuối**: 2026-03-18  
**Ngôn Ngữ**: Tiếng Việt 100%
