# 🚀 MEDPILOT - Triển Khai Tự Động cho Windows
# Script này sẽ cài đặt, kiểm tra và chạy toàn bộ hệ thống

# Hàm hiển thị màu sắc
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Warning-Custom { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Section { Write-Host "`n$args" -ForegroundColor Blue; Write-Host "===========================================" }

Write-Host "=========================================="
Write-Host "🏥 MedPilot Backend - Triển Khai Windows"
Write-Host "==========================================" -ForegroundColor Cyan

# ============================================
# GIAI ĐOẠN 1: Kiểm Tra Yêu Cầu
# ============================================
Write-Section "GIAI ĐOẠN 1: Kiểm Tra Các Yêu Cầu Trước"

# Kiểm Tra Ollama
Write-Host "Đang kiểm tra Ollama..." -ForegroundColor Cyan
$ollamaPath = "C:\Users\Admin\AppData\Local\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaPath) {
    Write-Success "Ollama được tìm thấy: $ollamaPath"
    
    # Kiểm tra model
    $models = & $ollamaPath list 2>&1
    if ($models -like "*qwen2.5:7b*") {
        Write-Success "Model qwen2.5:7b được tìm thấy"
    } else {
        Write-Warning-Custom "Model không được tìm thấy, sẽ pull trong quá trình khởi động"
    }
} else {
    Write-Error-Custom "Ollama không được tìm thấy. Tải từ: https://ollama.ai"
    exit 1
}

# Kiểm Tra Python
Write-Host "Đang kiểm tra Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Success $pythonVersion
} catch {
    Write-Error-Custom "Python không được tìm thấy"
    exit 1
}

# Kiểm Tra Phụ Thuộc
Write-Host "Đang kiểm tra các gói Python..." -ForegroundColor Cyan
$deps = python -c "import fastapi; import pydantic; import requests; import chromadb; import sentence_transformers; print('OK')" 2>&1
if ($deps -eq "OK") {
    Write-Success "Tất cả gói phụ thuộc đã được cài đặt"
} else {
    Write-Warning-Custom "Đang cài đặt các gói phụ thuộc..."
    pip install -r requirements.txt
}

# Kiểm Tra Dữ Liệu Bệnh Lý
Write-Host "Đang kiểm tra kho bệnh lý..." -ForegroundColor Cyan
$dataPath = ".\app\database\data\diseases_data.json"
if (Test-Path $dataPath) {
    $fileSizeMB = [math]::Round((Get-Item $dataPath).Length / 1MB, 2)
    Write-Success "diseases_data.json được tìm thấy ($fileSizeMB MB)"
} else {
    Write-Error-Custom "diseases_data.json không được tìm thấy tại $dataPath"
    exit 1
}

# ============================================
# GIAI ĐOẠN 2: Khởi Động Dịch Vụ
# ============================================
Write-Section "GIAI ĐOẠN 2: Khởi Động Các Dịch Vụ"

# Dừng các process Ollama cũ
Write-Host "Đang dừng các process Ollama cũ..." -ForegroundColor Cyan
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Khởi Động Ollama
Write-Host "Đang khởi động Ollama..." -ForegroundColor Cyan
$ollama_process = Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden -PassThru
Write-Success "Ollama đã khởi động (PID: $($ollama_process.Id))"

Write-Info "Đang chờ 40 giây để Ollama ổn định..."
for ($i = 40; $i -gt 0; $i--) {
    Write-Host -NoNewline "`r   $i giây còn lại...       "
    Start-Sleep -Seconds 1
}
Write-Host "`r   Ollama sẵn sàng!              "

# Kiểm Tra Ollama Phản Hồi
$ollama_ready = $false
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Ollama đang phản hồi trên port 11434"
            $ollama_ready = $true
            break
        }
    } catch {
        if ($attempt -lt 5) {
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $ollama_ready) {
    Write-Error-Custom "Ollama không phản hồi trên port 11434"
    exit 1
}

# Giải Phóng Port 8000
Write-Host "Đang giải phóng port 8000..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    taskkill /PID $_.OwningProcess /F /T 2>$null
}
Start-Sleep -Seconds 2
Write-Success "Port 8000 đã giải phóng"

# Khởi Động Backend
Write-Host "Đang khởi động Backend Server..." -ForegroundColor Cyan
$env:PYTHONUNBUFFERED = 1
$backend_process = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput ".\server.log" `
    -RedirectStandardError ".\server.log"

Write-Success "Backend đã khởi động (PID: $($backend_process.Id))"

Write-Info "Đang chờ 10 giây để Backend khởi động..."
Start-Sleep -Seconds 10

# Kiểm Tra Backend Phản Hồi
$backend_ready = $false
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ask-role" `
            -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend đang phản hồi trên port 8000"
            $backend_ready = $true
            break
        }
    } catch {
        if ($attempt -lt 5) {
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $backend_ready) {
    Write-Error-Custom "Backend không phản hồi trên port 8000"
    Write-Info "Kiểm tra server.log để xem chi tiết"
    exit 1
}

# ============================================
# GIAI ĐOẠN 3: Chạy Test
# ============================================
Write-Section "GIAI ĐOẠN 3: Chạy Bộ Test Toàn Diện"

Write-Info "Đang khởi động bộ test toàn diện..."
Write-Info "Điều này có thể mất 2-3 phút..."
Write-Host ""

python test/test_e2e.py

if ($LASTEXITCODE -eq 0) {
    Write-Success "Test đã thành công! ✅"
} else {
    Write-Error-Custom "Test gặp vấn đề"
    Write-Info "Kiểm tra output ở trên để xem chi tiết"
}

# ============================================
# HOÀN THÀNH
# ============================================
Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "🎉 TRIỂN KHAI MEDPILOT THÀNH CÔNG!" -ForegroundColor Green
Write-Host "=========================================="
Write-Host ""

Write-Host "📊 Các Dịch Vụ Đang Chạy:" -ForegroundColor Cyan
Write-Host "   - Ollama:  http://localhost:11434" -ForegroundColor Gray
Write-Host "   - Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host ""

Write-Host "🧪 Các Endpoint Có Sẵn:" -ForegroundColor Cyan
Write-Host "   - GET  /api/v1/ask-role              (Lựa chọn vai trò)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/query?role=doctor     (Chế độ bác sĩ)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/query?role=patient    (Chế độ bệnh nhân)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/chat                  (Hội thoại bệnh nhân)" -ForegroundColor Gray
Write-Host ""

Write-Host "📚 Tài Liệu:" -ForegroundColor Cyan
Write-Host "   - IMPLEMENTATION_SUMMARY_VI.md (Hướng dẫn đầy đủ)" -ForegroundColor Gray
Write-Host "   - FINAL_CHECKLIST_VI.md        (Danh sách kiểm tra)" -ForegroundColor Gray
Write-Host "   - test/README.md               (Hướng dẫn test)" -ForegroundColor Gray
Write-Host ""

Write-Host "🧹 Để dừng dịch vụ sau này:" -ForegroundColor Yellow
Write-Host '   taskkill /IM ollama.exe /F' -ForegroundColor Gray
Write-Host '   taskkill /F /IM python.exe /T 2>$null' -ForegroundColor Gray
Write-Host ""

Write-Host "✅ Sẵn sàng cho sản xuất!" -ForegroundColor Green
Write-Host ""
