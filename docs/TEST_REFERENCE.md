# 🎯 QUICK REFERENCE - Chạy Test Local → E2E → Interactive

## ⚡ TL;DR (30 giây setup)

### Terminal 1: Ollama
```powershell
ollama serve
# Chờ: Listening on 127.0.0.1:11434
```

### Terminal 2: Backend
```powershell
cd "c:\Dự án\Medplot\medpilot_remind"
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

### Terminal 3: Run Tests
```powershell
cd "c:\Dự án\Medplot\medpilot_remind"
.\.venv\Scripts\Activate.ps1

# Option A: Automated test (5 min)
python test/test_e2e.py

# Option B: Interactive test (10 min)
python test/test_interactive.py

# Option C: Both (guided)
python run_tests.py
```

---

## 📋 Test Files Explained

| File | Type | Purpose | Time |
|------|------|---------|------|
| `test_e2e.py` | ✅ Automated | Full regression testing (4 test cases) | ~1 min |
| `test_interactive.py` | 💬 Manual | User-driven testing + demo | ~10 min |
| `run_tests.py` | 🤖 Helper | Guided setup + test runner | ~5 min |

---

## 🧪 What Each Test Does

### test_e2e.py (Automated)
```
✅ TEST 1: Role Selection
   - Kích hoạt /api/v1/ask-role
   - Kiểm tra nhận được ['doctor', 'patient']

✅ TEST 2: Doctor Flow
   - POST /api/v1/query with doctor mode
   - Kiểm tra response từ LLM

✅ TEST 3: Patient Flow (Suite)
   - Multiple patient questions with chat endpoint
   - Medication warning detection
   - Out-of-scope handling

✅ TEST 4: API Robustness
   - Edge case handling (empty messages, whitespace)
```

### test_interactive.py (Interactive)
```
💬 TEST 1: Role Selection (Auto)
   - Display role prompt
   - Show available options

💬 TEST 2: Doctor Mode (Manual)
   - Nhập câu hỏi bác sĩ hoặc 'skip'
   - Nhận response từ AI

💬 TEST 3: Patient Chat (Interactive Loop)
   - Loop: nhập câu → nhận response → nhập câu khác → ... → exit
   - Medication warning detection
   - Out-of-scope detection
```

---

## ✅ Expected Results

### ✅ SUCCESS Indicators:
```
test_e2e.py:
  ✅ TEST 1: Role Selection → PASS
  ✅ TEST 2: Doctor Flow → PASS
  ✅ TEST 3: Patient Flow → PASS
  ✅ TEST 4: API Robustness → PASS
  
  RAM usage: < 2GB
  Test time: ~60 seconds
  Exit code: 0

test_interactive.py:
  ✅ TEST 1: Role Selection → Displayed
  ✅ TEST 2: Doctor Mode → Response shown
  ✅ TEST 3: Patient Chat → Conversation logged
  
  No crashes or errors
  All responses coherent in Vietnamese
```

### ❌ FAILURE Indicators:
```
❌ HTTP 500 with {"detail": ""}
   → Server error (check logs in Terminal 2)

❌ "Could not connect to http://localhost:8000"
   → Backend not running (check Terminal 2)

❌ "Could not connect to Ollama"
   → Ollama not running (check Terminal 1)

❌ "ModuleNotFoundError: sentence_transformers"
   → Dependencies not installed (rerun: pip install -r requirements.txt)

❌ "Port 8000 already in use"
   → Kill python: Get-Process python | Stop-Process -Force
```

---

## 🎮 Interactive Chat Examples

### Patient Mode - Valid Dermatology Questions:
```
✅ "Mụn trứng cá là gì?" → Good (dermatology question)
✅ "Có cách phòng ngừa mụn không?" → Good (dermatology)
✅ "Triệu chứng viêm da cơ địa?" → Good (dermatology)
✅ "Làm sao để chăm sóc da lành?" → Good (dermatology)
```

### Patient Mode - Special Cases:
```
⚠️ "Nên mua kem nào để trị mụn?" → Medication warning triggered
   → AI will respond with warning: "Không tự mua thuốc..."
   
⛔ "Hôm nay thời tiết thế nào?" → Out of scope
   → AI will respond: "Xin lỗi, tôi chỉ được đào tạo về da liễu..."
   
⛔ "Bây giờ mấy giờ?" → Out of scope
   → Same out-of-scope response
```

### Doctor Mode - Valid Questions:
```
✅ "Bệnh nhân nổi đỏ ngứa 2 tuần. Chẩn đoán gì?" → Good
✅ "Triệu chứng viêm da tiếp xúc?" → Good
✅ "Phân biệt giữa mụn và nổi mẩn?" → Good
```

---

## 📊 Performance Targets

After optimization, you should see:

```
Startup Time:
  - Before: ~30-40 seconds (OOM risk)
  - After:  ~2-3 seconds ✅

Per Query Memory:
  - Before: +1-2 GB extra
  - After:  +200-300 MB ✅

RAM Usage (During Test):
  - Before: 5-8 GB (crash risk)
  - After:  1-2 GB ✅

Query Response Time:
  - First:  2-3 seconds
  - Cached: <1 second ✅

Test Completion:
  - Before: ❌ OOM crash
  - After:  ✅ ~60 seconds ✅
```

---

## 🔧 Troubleshooting Quick Fixes

### Symptom: Window terminated unexpectedly (oom)
```powershell
# 1. Kill everything
Get-Process python,ollama | Stop-Process -Force -EA SI

# 2. Close VSCode, restart it

# 3. Wait 30 seconds

# 4. Restart from scratch
```

### Symptom: "ModuleNotFoundError"
```powershell
# Reinstall dependencies
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

### Symptom: "Port 8000 already in use"
```powershell
# Kill the process holding port
Get-Process python | Stop-Process -Force
Start-Sleep -Seconds 5
# Retry backend start
```

### Symptom: Keys seem to hang or tests take forever
```powershell
# Check Ollama responsiveness
curl http://localhost:11434/api/tags

# If slow: restart Ollama in Terminal 1
```

---

## 📚 File References

**Key Files:**
- 📄 `COMPLETE_TEST_GUIDE.md` - Detailed step-by-step guide (this is you are here!)
- 📄 `QUICK_START.md` - Quick local setup
- 📄 `OPTIMIZATION_GUIDE.md` - Technical optimization details
- 🐍 `run_tests.py` - Automated test runner

**Test Files:**
- `test/test_e2e.py` - Automated comprehensive test
- `test/test_interactive.py` - Interactive manual test
- `test/test_debug.py` - Debug individual endpoints

**Config Files:**
- `.env` - Environment variables (optimized)
- `requirements.txt` - Python dependencies (optimized)
- `app/config.py` - Application config

---

## 🚀 Next Steps

After successful test completion:

1. ✅ Verify all 4 E2E tests pass
2. ✅ Verify interactive chat works smoothly
3. ✅ Monitor RAM (should stay < 2GB)
4. ✅ Check response quality (relevant, coherent)
5. ✅ Test with different questions
6. ✅ Consider deployment

---

## 📞 Quick Answers

**Q: How long does it take to run all tests?**
A: ~10-15 minutes (5 min E2E + 10 min interactive + setup)

**Q: Do I need 3 terminals?**
A: Yes - Terminal 1 (Ollama), Terminal 2 (Backend), Terminal 3 (Tests)

**Q: Can I run both tests at the same time?**
A: No - run test_e2e.py first, then test_interactive.py

**Q: What if Ollama crashes?**
A: Restart in Terminal 1: `ollama serve`

**Q: What if backend crashes?**
A: Restart in Terminal 2: `python -m uvicorn app.main:app --port 8000 --reload`

**Q: What if I get a memory error?**
A: Close other apps, wait 30 seconds, restart from fresh venv

**Q: How do I know if tests passed?**
A: Look for "✅ ALL TESTS PASSED!" or "✅ PASS" messages

---

## 💡 Pro Tips

```powershell
# Monitor RAM during testing
while ($true) { 
    Get-Process python | Select-Object Name, @{Name="RAM (MB)"; Expression={[math]::Round($_.WorkingSet/1MB)}}
    Start-Sleep -Seconds 1
}

# Check if services are running
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/api/v1/ask-role  # Backend

# Kill all python processes (nuclear option)
Get-Process python,pythonw | Stop-Process -Force -ErrorAction SilentlyContinue

# Install specific package version
pip install sentence-transformers==2.2.2
```

---

**🎉 Ready? Start with Terminal 1: `ollama serve` ↑**
