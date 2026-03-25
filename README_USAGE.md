
# Hướng dẫn sử dụng MedPilot - Clinical Decision Support System

Dự án MedPilot là công cụ hỗ trợ bác sĩ và bệnh nhân chuyên về da liễu, sử dụng AI (Gemini) để trích xuất thông tin lâm sàng và đưa ra các gợi ý quy tắc y khoa.

## 🚀 1. Cài đặt ban đầu

### Backend (Python)
1. Cài đặt Python 3.9+
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Cấu hình file `.env` (không được push lên GitHub):
   ```env
   GOOGLE_API_KEY=AIzaSy... (Khóa Gemini của bạn)
   GEMINI_MODEL=gemini-2.5-flash
   DB_PATH=chroma_db
   ```

### Frontend (React + Vite)
1. Di chuyển vào thư mục frontend: `cd frontend`
2. Cài đặt node modules:
   ```bash
   npm install
   ```

---

## 🛠️ 2. Cách chạy ứng dụng

Mở 2 cửa sổ terminal riêng biệt:

**Terminal 1 (Backend):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
Truy cập ứng dụng tại: `http://localhost:5173`

---

## 👨‍⚕️ 3. Chế độ Bác sĩ (Doctor Mode)

1.  **Ghi âm/Tải file**: Nhấn nút mic để ghi âm cuộc hội thoại bác sĩ - bệnh nhân hoặc tải lên file `.webm`.
2.  **Trích xuất dữ liệu (3-Layer Pipeline)**: AI sẽ tự động trích xuất các thông tin: Lý do khám, triệu chứng, tiền sử, vị trí tổn thương...
3.  **Gợi ý quy tắc (Rule-based)**:
    - Hệ thống tự động so khớp các dữ liệu trích xuất với bộ quy tắc y khoa.
    - **Cảnh báo Red Flags**: Hiển thị bảng màu đỏ nhấp nháy "KHẨN CẤP" nếu phát hiện dấu hiệu nguy hiểm (sốt, lan nhanh, mủ...).
    - **Gợi ý chẩn đoán**: Đưa ra các "Cân nhắc lâm sàng" (Possible Considerations).
    - **Câu hỏi bổ sung**: Gợi ý các câu hỏi bác sĩ nên hỏi thêm để làm rõ bệnh cảnh.

---

## 🚑 4. Khắc phục sự cố (Troubleshooting)

### Lỗi RAG (Gợi ý chẩn đoán không hiện hoặc báo 500)
Nếu bạn thấy lỗi `InternalError - Error loading hnsw segment reader` hoặc suggest bị trống, hãy chạy lệnh sau để làm sạch và xây dựng lại cơ sở dữ liệu tri thức:

```bash
python scripts/reset_rag_database.py
```
*(Lưu ý: Cần tắt backend server trước khi chạy lệnh này)*

### Kiểm tra Logic quy tắc
Bạn có thể kiểm tra bộ quy tắc lâm sàng mà không cần chạy toàn bộ app bằng lệnh:
```bash
python scripts/verify_rule_logic.py
```

---

## 📁 5. Quy trình đẩy code lên GitHub (Git Workflow)

Để đẩy code lên GitHub an toàn (không lộ API Key và không kèm rác cache):

1.  **Dọn dẹp cache (nếu cần)**:
    ```bash
    git rm -r --cached .env app/__pycache__ chroma_db logs/*.log
    ```
2.  **Thêm các thay đổi**:
    ```bash
    git add .
    ```
3.  **Commit**:
    ```bash
    git commit -m "Tính năng: Triển khai gợi ý quy tắc và pipeline trích xuất 3 lớp"
    ```
4.  **Push**:
    ```bash
    git push origin main
    ```

---

*MedPilot — Hỗ trợ quyết định lâm sàng thông minh & an toàn.*
