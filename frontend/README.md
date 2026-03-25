# MedPilot Frontend

Frontend React cho MedPilot - Trợ lý AI Da liễu

## Yêu cầu

- Node.js >= 18
- Backend MedPilot đang chạy ở `http://localhost:8000`

## Cài đặt

```bash
cd frontend
npm install
```

## Chạy

```bash
npm run dev
```

Mở trình duyệt: http://localhost:3000

## Tính năng

### Chế độ Bác sĩ
- Bắt đầu phiên khám mới
- Ghi âm hoặc tải lên audio hội thoại
- Tự động chuyển giọng nói thành văn bản (PhoWhisper)
- Trích xuất thông tin cấu trúc từ transcript
- Gợi ý chẩn đoán phân biệt
- Hiển thị red flags và lưu ý lâm sàng
- Chỉnh sửa trực tiếp trên giao diện
- Lưu hồ sơ sau khi duyệt

### Chế độ Bệnh nhân
- Chat với AI về các vấn đề da liễu
- Ghi âm câu hỏi bằng giọng nói
- Nhận câu trả lời dễ hiểu
- Cảnh báo an toàn khi hỏi về thuốc
- Khuyến nghị đi khám bác sĩ

## Cấu trúc

```
frontend/
├── src/
│   ├── components/
│   │   └── RoleSelection.jsx   # Chọn vai trò
│   ├── pages/
│   │   ├── DoctorDashboard.jsx # Giao diện bác sĩ
│   │   └── PatientChat.jsx     # Giao diện bệnh nhân
│   ├── services/
│   │   └── api.js              # API calls
│   ├── styles/
│   │   └── index.css           # Global styles
│   ├── App.jsx
│   └── main.jsx
└── package.json
```

## API Endpoints

- `POST /api/v1/query` - Query RAG
- `POST /api/v1/chat` - Chat cho bệnh nhân
- `POST /api/v1/speech/transcribe` - Transcribe audio
- `POST /api/v1/speech/extract` - Trích xuất thông tin

## Lưu ý

- Backend phải chạy ở `http://localhost:8000`
- Colab notebooks phải chạy cho PhoWhisper và vLLM
