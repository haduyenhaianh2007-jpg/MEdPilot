# 🏥 MedPilot Backend - Triển Khai Hoàn Chỉnh

## ✅ Tóm Tắt Triển Khai

### 🎯 Kiến Trúc Hệ Thống

**Hệ thống có 2 chế độ riêng biệt:**

#### 1️⃣ **Chế Độ Bác Sĩ** (`/api/v1/query?role=doctor`)
- **Đầu vào**: Câu hỏi/mô tả triệu chứng
- **Xử lý**: RAG lấy kho bệnh → LLM tạo gợi ý chẩn đoán chi tiết
- **Đầu ra**: Phản hồi y tế chuyên sâu:
  - Chẩn đoán nghi ngờ chính
  - Chẩn đoán phân biệt
  - Bằng chứng lâm sàng hỗ trợ
- **Ngôn ngữ**: Tiếng Việt, chuyên sâu/kỹ thuật
- **Nhiệt độ**: 0.5 (xác định cao, chính xác hơn)
- **Token tối đa**: 2000 (phản hồi chi tiết)

#### 2️⃣ **Chế Độ Bệnh Nhân** (`/api/v1/query?role=patient` hoặc `/api/v1/chat`)
- **Đầu vào**: Hỏi đáp liên tục
- **Xử lý**: 
  - Kiểm tra phạm vi da liễu
  - Phát hiện ý định mua thuốc
  - Lấy dữ liệu RAG nếu trong phạm vi
  - Tạo phản hồi với lịch sử hội thoại
- **Đầu ra**: Phản hồi giáo dục:
  - Giải thích đơn giản
  - KHÔNG chẩn đoán (chỉ thông tin chung)
  - Cảnh báo khi phát hiện mua thuốc
  - Khuyên đi khám bác sĩ
- **Ngôn ngữ**: Tiếng Việt, thân thiện/dễ hiểu
- **Đặc biệt**: 
  - Từ chối câu hỏi ngoài da liễu
  - Cảnh báo khi phát hiện dấu hiệu mua thuốc
- **Lưu lịch sử**: Trong bộ nhớ (có thể nâng cấp lên DB)

#### 3️⃣ **Lựa Chọn Vai Trò** (`GET /api/v1/ask-role`)
- Trả về tin nhắn với các tùy chọn ("bác sĩ" hoặc "bệnh nhân")
- Sử dụng cho luồng UX ban đầu

---

## 📁 Cấu Trúc Dự Án

```
medpilot_remind/
├── app/
│   ├── main.py                    ✅ CẬP NHẬT - Định tuyến theo vai trò
│   ├── prompts.py                 ✅ CẬP NHẬT - Prompt bác sĩ & bệnh nhân
│   ├── schemas.py                 ✅ CẬP NHẬT - Model phản hồi mới
│   ├── llm_service.py             ✅ (không thay đổi - chạy tốt)
│   ├── rag_engine.py              ✅ (không thay đổi - chạy tốt)
│   ├── config.py                  ✅ (không thay đổi)
│   ├── test.json                  ✅ Dữ liệu test mẫu
│   └── database/
│       └── data/
│           └── diseases_data.json  ✅ 219 bệnh lý, 6.49MB
│
├── test/                          ✅ MỚI - Thư mục test
│   ├── README.md                  ✅ Tài liệu test (tiếng Việt)
│   ├── test_doctor_mode.py        ✅ Test chế độ bác sĩ
│   ├── test_patient_mode.py       ✅ Test chế độ bệnh nhân
│   └── test_e2e.py                ✅ Test end-to-end
│
├── chroma_db/                     ✅ CSDL vector (tự động tạo)
├── IMPLEMENTATION_SUMMARY_VI.md   ✅ Hướng dẫn kỹ thuật (Tiếng Việt)
├── FINAL_CHECKLIST_VI.md          ✅ Danh sách triển khai (Tiếng Việt)
├── DEPLOY_WINDOWS.ps1             ✅ Script Windows
├── QUICKSTART.sh                  ✅ Script Linux/Mac
└── requirements.txt               ✅ Các gói phụ thuộc
```

---

## 🔧 Các File Đã Được Sửa Đổi

### 1. `app/prompts.py` - Thêm Prompt Mới
✅ `DOCTOR_MODE_SYSTEM_VI` - Prompt chẩn đoán bác sĩ
✅ `PATIENT_MODE_SYSTEM_VI` - Prompt giáo dục bệnh nhân
✅ `DERMATOLOGY_SCOPE_CHECK_VI` - Kiểm tra phạm vi
✅ Cộng thêm phiên bản tiếng Anh

### 2. `app/schemas.py` - Thêm Model Mới
✅ `DoctorQueryRequest` - Đầu vào chế độ bác sĩ
✅ `DoctorQueryResponse` - Đầu ra chế độ bác sĩ
✅ `PatientChatResponse` - Đầu ra chế độ bệnh nhân (có cảnh báo thuốc)
✅ Cập nhật model hiện có để tương thích

### 3. `app/main.py` - Cập Nhật Lớn
✅ Import `Query` từ fastapi cho tham số role
✅ Cập nhật endpoint `/api/v1/query`:
   - Hỗ trợ tham số query `role`
   - Lựa chọn prompt hệ thống theo vai trò
   - Nhiệt độ & max_tokens khác nhau cho mỗi vai trò
   - Logging rõ ràng cho mỗi chế độ
✅ Cập nhật endpoint `/api/v1/chat`:
   - Phát hiện cảnh báo mua thuốc bằng `check_medication_intent()`
   - Kiểm tra phạm vi da liễu tốt hơn
   - Phản hồi cảnh báo mua thuốc
   - Quản lý lịch sử hội thoại
✅ Thêm hàm `check_medication_intent()`
✅ Cải tiến `is_dermatology_question()` với nhiều từ khóa hơn

---

## 🧪 Test Bao Gồm

### `test/test_doctor_mode.py`
- ✅ Test single query (một câu hỏi)
- ✅ Test multi-turn (nhiều câu hỏi liên tiếp)
- ✅ Xác minh RAG retrieval
- ✅ Xác minh LLM response

### `test/test_patient_mode.py`
- ✅ Test Q&A thông thường (câu hỏi về da liễu)
- ✅ Test cảnh báo mua thuốc (phát hiện & từ chối)
- ✅ Test phạm vi ngoài da liễu (từ chối với khuyên)
- ✅ Test lịch sử hội thoại

### `test/test_e2e.py`
- ✅ Test flow hoàn chỉnh: Role Selection → Query → Response
- ✅ Test cả hai chế độ trong một chạy
- ✅ So sánh thời gian phản hồi

---

## 🚀 Cách Chạy (TRIỂN KHAI CUỐI CÙNG)

### **Người Dùng Windows - Phương Pháp Được Khuyến Nghị**

```powershell
# Chạy script triển khai tự động
cd "c:\Dự án\Medplot\medpilot_remind"
powershell -ExecutionPolicy Bypass -File DEPLOY_WINDOWS.ps1
```

**Script này sẽ:**
1. ✅ Kiểm tra các yêu cầu (Ollama, Python, phụ thuộc)
2. ✅ Khởi động dịch vụ Ollama
3. ✅ Khởi động server Backend
4. ✅ Chờ cả hai dịch vụ sẵn sàng
5. ✅ Chạy bộ test hoàn chỉnh
6. ✅ Hiển thị kết quả và trạng thái

---

## 🧪 Test Thủ Công (Nếu Cần Thiết)

### Terminal 1: Khởi Động Ollama
```bash
ollama serve
# Chờ ~30s để dịch vụ ổn định
```

### Terminal 2: Khởi Động Backend
```bash
cd "c:\Dự án\Medplot\medpilot_remind"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 3: Chạy Test
```bash
cd "c:\Dự án\Medplot\medpilot_remind"

# Chạy tất cả test (được khuyến nghị)
python test/test_e2e.py

# Hoặc chạy riêng lẻ
python test/test_doctor_mode.py
python test/test_patient_mode.py
```

---

## ✅ Tiêu Chí Thành Công

| Tiêu Chí | Yêu Cầu | Trạng Thái |
|---------|---------|-----------|
| **Chế Độ Bác Sĩ** | Phản hồi kỹ thuật chi tiết | ✅ |
| **Chế Độ Bệnh Nhân** | Phản hồi thân thiện, KHÔNG chẩn đoán | ✅ |
| **Cảnh Báo Mua Thuốc** | Phát hiện & từ chối hiệu quả | ✅ |
| **Phạm Vi Da Liễu** | Từ chối câu hỏi ngoài da liễu | ✅ |
| **Lịch Sử Hội Thoại** | Giữ ngữ cảnh giữa các câu hỏi | ✅ |
| **Thời Gian Phản Hồi** | < 10 giây cho mỗi câu | ✅ |
| **RAG Retrieval** | Lấy được bệnh lý liên quan | ✅ |

---

## 📝 Ghi Chú Kỹ Thuật

- **LLM Model**: Qwen2.5:7b (nhanh hơn llama2)
- **Vector DB**: ChromaDB với MiniLM embedding
- **Framework**: FastAPI + Uvicorn
- **Bất động sản Sinh**: GPT-style prompting với role-specific templates
- **Lưu Trữ Chat**: In-memory dicts (upgrade lên DB nếu cần)

---

## 🔗 Tài Liệu Liên Quan

- [FINAL_CHECKLIST_VI.md](FINAL_CHECKLIST_VI.md) - Danh sách kiểm tra cuối cùng
- [DEPLOY_WINDOWS.ps1](DEPLOY_WINDOWS.ps1) - Script triển khai Windows
- [QUICKSTART.sh](QUICKSTART.sh) - Script triển khai Linux/Mac
- [test/README.md](test/README.md) - Hướng dẫn test chi tiết
