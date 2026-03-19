# 📚 HƯỚNG DẪN HOÀN CHỈNH: Chạy Test từ Local đến Interactive

**Thời gian ước lượng:** 15-20 phút

---

## 🎯 ROADMAP

```
STEP 1: Setup Local Environment (5 min)
    ↓
STEP 2: Khởi động Ollama (2 min)
    ↓
STEP 3: Khởi động Backend Server (2 min)
    ↓
STEP 4: Chạy Automated Test (test_e2e.py) (5 min)
    ↓
STEP 5: Chạy Interactive Test (test_interactive.py) (10 min)
    ↓
✅ HOÀN THÀNH
```

---

# 🚀 STEP 1: Setup Local Environment

## 1.1 Mở PowerShell Terminal

```powershell
# Mở terminal mới
# Windows: Ctrl + ` hoặc right-click → "Open PowerShell here"

# Điều hướng tới project
cd "c:\Dự án\Medplot\medpilot_remind"

# Kiểm tra tệp
dir

# Expected output:
# app/  tests/  test/  docs/  .env  requirements.txt  ...
```

## 1.2 Tạo Virtual Environment Mới (Fresh Start)

```powershell
# Xoá venv cũ (nếu có)
if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }

# Tạo venv mới
python -m venv .venv

# Kiểm tra
dir .venv

# Expected: Thư mục .venv được tạo
```

## 1.3 Kích Hoạt Virtual Environment

```powershell
# Windows Activation
.\.venv\Scripts\Activate.ps1

# Expected: Dòng lệnh thay đổi thành:
# (.venv) PS C:\Dự án\Medplot\medpilot_remind>
```

**Nếu bị lỗi "execution of scripts is disabled":**
```powershell
# Chạy lần này thôi:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Sau đó activate lại:
.\.venv\Scripts\Activate.ps1
```

## 1.4 Cài Đặt Dependencies (Optimized)

```powershell
# Cài từ requirements.txt (đã tối ưu)
pip install -r requirements.txt

# Xem tiến trình:
# Collecting numpy==1.26.4
# Collecting scikit-learn==1.4.2
# ...

# Successfully installed [packages]

# Kiểm tra cài đặt
pip list | Select-String "fastapi|sentence-transformers|chromadb"

# Expected output:
# fastapi                    0.104.1
# sentence-transformers       2.2.2
# chromadb                    0.4.18
```

## 1.5 Kiểm Tra Config

```powershell
# Xem .env file
cat .env | Select-String "EMBEDDING_MODEL|TOP_K|MAX_TOKENS"

# Expected:
# EMBEDDING_MODEL=sentence-transformers/distiluse-base-multilingual-cased-v2
# TOP_K=2
# MAX_TOKENS=500
```

✅ **STEP 1 HOÀN THÀNH**

---

# 🌐 STEP 2: Khởi Động Ollama Service

**📌 Mở Terminal Mới (Terminal 1 - Giữ Chạy)**

```powershell
# Terminal 1 - GIỮ CHẠY SỐT ĐỦ CÁC BƯỚC
ollama serve

# Chờ 10-15 giây...
# ✅ Expected output:
# Listening on 127.0.0.1:11434
# (ctrl+c để stop, nhưng ĐỪNG STOP!)
```

**Nếu không có Ollama:**
```powershell
# Download: https://ollama.ai
# Hoặc PowerShell: winget install Ollama
```

✅ **STEP 2 HOÀN THÀNH - Giữ terminal này chạy**

---

# ⚙️ STEP 3: Khởi Động Backend Server

**📌 Mở Terminal Mới (Terminal 2 - Giữ Chạy)**

```powershell
# Terminal 2 - GIỮ CHẠY
cd "c:\Dự án\Medplot\medpilot_remind"

# Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Khởi động server (⚡ nhanh hơn lúc trước)
python -m uvicorn app.main:app --port 8000 --reload

# Chờ ~3 giây...
# ✅ Expected output:
# 📥 Loading embedding model...
# 💾 Initializing Chroma DB...
# 🚀 Initializing services...
# ✅ Backend ready!
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Uvicorn running on http://0.0.0.0:8000
# (ctrl+c để stop, nhưng ĐỪNG STOP!)
```

**Kiểm tra Server Healthy:**
```powershell
# Terminal 3 - Kiểm tra (hoặc mở browser tab mới)
curl http://localhost:8000/docs

# Expected: FastAPI Swagger UI tải được
# Hoặc direct curl:
curl http://localhost:8000/api/v1/ask-role

# Expected:
# {"message":"👋 Xin chào...","options":["doctor","patient"],"timestamp":"..."}
```

✅ **STEP 3 HOÀN THÀNH - Giữ terminal này chạy**

---

# 🧪 STEP 4: Chạy Automated Test (test_e2e.py)

**📌 Mở Terminal Mới (Terminal 3)**

```powershell
# Terminal 3 - RUN TEST
cd "c:\Dự án\Medplot\medpilot_remind"

# Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Chạy test_e2e
python test/test_e2e.py

# Chờ ~60 giây để test chạy...
```

## Expected Output:

```
============================================================
✅ API đang chạy
============================================================

============================================================
1️⃣ TEST: Role Selection Endpoint
============================================================
✅ Status: 200
📋 Message: 👋 Xin chào! Chào mừng đến với MedPilot...
🔘 Options: ['doctor', 'patient']
✅ PASS

============================================================
2️⃣ TEST: Doctor Flow
============================================================
❓ Query: Bệnh nhân nổi đỏ, ngứa hai bàn tay kéo dài 2 tuần
✅ Status: 200
📝 Answer: [Doctor mode response...]
✅ PASS

============================================================
3️⃣ TEST: Patient Flow
============================================================
Q1: Mụn trứng cá là gì?
✅ Status: 200 | Chunks: 2
✅ PASS

Q2: Có cách phòng ngừa không?
✅ Status: 200 | Chunks: 1
✅ PASS

Q3: Mua kem gì để trị?
⚠️  Medication Warning Detected
✅ PASS

Q4: Hôm nay thời tiết thế nào?
⛔ Out of Scope
✅ PASS

============================================================
4️⃣ TEST: API Robustness
============================================================
Empty message → 200 ✅
Whitespace only → 200 ✅
Long message → 200 ✅
✅ PASS

============================================================
✅ ALL TESTS PASSED!
============================================================
```

## RAM Monitoring (Khi đang test):
```powershell
# Mở Task Manager (Ctrl + Shift + Esc)
# Hoặc terminal khác:
while ($true) { 
    Get-Process python | Select-Object Name, @{Name="RAM (MB)"; Expression={[math]::Round($_.WorkingSet/1MB)}}
    Start-Sleep -Seconds 2
}

# Expected: RAM không vượt quá 2GB ✅
```

✅ **STEP 4 HOÀN THÀNH - Nếu tất cả PASS → Tiếp tục Step 5**

---

# 💬 STEP 5: Chạy Interactive Test (test_interactive.py)

**📌 Terminal 3 (hoặc Terminal mới)**

```powershell
# Terminal 3
cd "c:\Dự án\Medplot\medpilot_remind"
.\.venv\Scripts\Activate.ps1

# Chạy interactive test
python test/test_interactive.py
```

## Cách Hoạt Động:

```
Bạn sẽ được hỏi tương tác từng bước. Hãy trả lời theo hướng dẫn của script.

TEST 1️⃣  - HỎI ROLE
  Show: Role selection prompt
  Action: [Tự động - không cần input từ bạn]

TEST 2️⃣  - DOCTOR MODE
  Prompt: "Nhập câu hỏi bác sĩ (hoặc 'skip' để bỏ qua):"
  Action: Nhập câu hỏi hoặc gõ 'skip'
  
  Example Doctor Questions:
  - Bệnh nhân nổi đỏ, ngứa 2 tuần. Chẩn đoán gì?
  - Triệu chứng của viêm da cơ địa là gì?
  
TEST 3️⃣  - PATIENT MODE (Interactive Chat)
  Prompt: "Nhập câu hỏi bệnh nhân (exit để thoát):"
  
  Chế độ Chat Liên Tục:
  - Gõ câu hỏi
  - Nhận response từ AI
  - Gõ tiếp câu hỏi khác HOẶC 'exit' để thoát
  
  Example Patient Questions:
  - Mụn trứng cá là gì?
  - Có cách phòng ngừa không?
  - Nên dùng kem gì?
  - Hôm nay thời tiết thế nào? (test out-of-scope)
```

## Sample Session:

```
======================================================================
  Test 1️⃣  - HỎI ROLE (Ask Role)
======================================================================

✅ Response Status: 200

📋 Message:
👋 Xin chào! Chào mừng đến với MedPilot Remind

Tôi là trợ lý AI chuyên về da liễu. Tôi có thể giúp bạn:
- 👨‍⚕️ Doctor Mode: Hỗ trợ chẩn đoán chi tiết (cho bác sĩ)
- 🧑‍🤝‍🧑 Patient Mode: Giáo dục sức khỏe (cho bệnh nhân)

🔘 Available Options: ['doctor', 'patient']

✅ TEST 1 PASSED


======================================================================
  Test 2️⃣  - DOCTOR MODE
======================================================================

Nhập câu hỏi bác sĩ (hoặc 'skip' để bỏ qua): 
> Bệnh nhân nổi đỏ ngứa 2 tuần thì chẩn đoán gì?

🤖 Processing doctor query...
⏱️  Latency: 2.34s

📝 Response:
Dựa trên triệu chứng của bệnh nhân (nổi đỏ, ngứa, kéo dài 2 tuần), 
những bệnh có thể xảy ra bao gồm:

1. Viêm da tiếp xúc - gây đỏ, ngứa, mẩn ngứa
2. Da liễu dị ứng - phản ứng từ thực phẩm, thuốc, chất hóa học
3. Viêm da cơ địa - viêm mạn tính, ngứa, đỏ,...)

✅ TEST 2 PASSED


======================================================================
  Test 3️⃣  - PATIENT INTERACTIVE CHAT
======================================================================

💬 Patient Chat Mode - Gõ 'exit' để dừng

Nhập câu hỏi bệnh nhân: 
> Mụn trứng cá là gì?

🤖 AI Response:
Mụn trứng cá (acne) là tình trạng da phổ biến khi lỗ chân lông bị tắc 
do dầu (sebum) và tế bào chết. Nó thường xuất hiện:
- Trên mặt, cổ, ngực, lưng
- Ở tuổi dậy thì (nhưng có thể xảy ra ở bất kỳ độ tuổi nào)

Nhập câu hỏi bệnh nhân:
> Có cách phòng ngừa mụn không?

🤖 AI Response:
Có! Dưới đây là các cách chăm sóc da để phòng tránh mụn:
1. Rửa mặt 2 lần/ngày với nước ấm và xà phòng nhẹ
2-7. [recommendations...]

Nhập câu hỏi bệnh nhân:
> Nên mua loại kem nào để trị mụn?

⚠️  MEDICATION PURCHASE INTENT DETECTED!
⚠️  CẢNH BÁO QUAN TRỌNG ⚠️

Bạn không nên TỰ MUA bất kỳ LOẠI THUỐC NÀO mà chưa tư vấn 
ý kiến bác sĩ da liễu!

[Lý do + hướng dẫn...]

Nhập câu hỏi bệnh nhân:
> Hôm nay thời tiết thế nào?

⛔ OUT OF SCOPE
Xin lỗi, tôi chỉ được đào tạo để trả lời các câu hỏi liên quan 
đến **da liễu**.

Nếu bạn có bất kỳ câu hỏi nào về:
- 🔬 Các bệnh da
- 💆 Chăm sóc da
- 🏥 Phòng ngừa và làm đẹp

[...]

Nhập câu hỏi bệnh nhân:
> exit

✅ TEST 3 PASSED - Chat mode completed

======================================================================
✅ ALL INTERACTIVE TESTS COMPLETED!
======================================================================
```

✅ **STEP 5 HOÀN THÀNH**

---

# 📊 So Sánh test_e2e.py vs test_interactive.py

| Aspect | test_e2e.py | test_interactive.py |
|--------|-------------|-------------------|
| **Loại Test** | Automated | Interactive/Manual |
| **Input** | Hard-coded test cases | User input (stdin) |
| **Thời gian** | ~60 giây | Tùy ý (người dùng quyết định) |
| **Mục đích** | CI/CD, regression testing | Manual validation, demo |
| **Kết quả** | PASS/FAIL summary | Detailed response output |
| **Phù hợp cho** | Development pipeline | User testing, demo |

---

# ✅ VERIFICATION CHECKLIST

Sau khi hoàn tất Step 5, kiểm tra:

- [ ] Terminal 1 (Ollama) chạy bình thường (Listening on 127.0.0.1:11434)
- [ ] Terminal 2 (Backend) chạy bình thường (Uvicorn running on 0.0.0.0:8000)
- [ ] test_e2e.py: Tất cả 4 test PASSED ✅
- [ ] test_interactive.py: Hoàn tất tất cả 3 test ✅
- [ ] RAM usage < 2GB ✅
- [ ] Không có OOM errors ✅
- [ ] VSCode không bị đơ ✅

---

# 🎓 Lý Thuyết - Các Mode Khác Nhau

## Role Selection Flow (Ask-Role)
```
User → GET /api/v1/ask-role
         ↓
      Server returns role options
         ↓
      User chooses: doctor or patient
```

## Doctor Mode (Query)
```
Doctor → POST /api/v1/query
         ↓
      Query: "Bệnh nhân nổi đỏ..."
         ↓
      System: Retrieve relevant diseases + LLM generate diagnostic support
         ↓
      Response: Detailed medical analysis (technical, for doctors)
```

## Patient Mode (Chat)
```
Patient → POST /api/v1/chat (Continuous)
         ↓
      Q1: "Mụn trứng cá là gì?"
         ↓
      System: Check scope + RAG retrieve + LLM generate
         ↓
      A1: "Mụn trứng cá là tình trạng da phổ biến..."
         ↓
      Q2: "Phòng ngừa sao?" (same conversation_id)
         ↓
      System: Use conversation history for context
         ↓
      A2: "Có! Dưới đây là các cách..."
         ↓
      Q3: "Mua kem gì?" (medication intent detected)
         ↓
      System: Medication warning!
         ↓
      A3: "⚠️ CẢNH BÁO - Không tự mua thuốc..."
```

---

# 🚀 Next Steps (Sau Hoàn Thành)

1. **Cleanup:** Ctrl+C ở Terminal 1 & 2 để stop services
2. **Verify:** Run test lại multiple times để ensure stability
3. **Performance:** Monitor RAM, check no memory leaks
4. **Deployment:** Ready for production if all tests pass ✅

---

# 🆘 Troubleshooting

### Error: "Could not connect to Ollama"
```powershell
# Terminal 1: Check Ollama running
curl http://localhost:11434/api/tags

# If fails: ollama serve
```

### Error: "Port 8000 already in use"
```powershell
# Kill python processes
Get-Process python | Stop-Process -Force

# Wait 5s
Start-Sleep -Seconds 5

# Retry backend start
```

### Error: "ModuleNotFoundError"
```powershell
# Verify venv activated
# Should show (.venv) in prompt

# Reinstall
pip install -r requirements.txt --force-reinstall
```

### Test takes > 2 minutes
```powershell
# Check Ollama response time
# Terminal: time curl http://localhost:11434/api/tags

# If slow: Restart Ollama (Terminal 1)
```

---

**🎉 Hoàn tất! Bạn đã chạy thành công từ Local → E2E → Interactive!**

Bất kỳ câu hỏi nào hãy báo cáo lỗi cùng Terminal output nhé! 🚀
