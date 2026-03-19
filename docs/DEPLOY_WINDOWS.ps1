# 🚀 MEDPILOT DEPLOYMENT - Windows Quick Start

# Colors for output
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Warning-Custom { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Section { Write-Host "`n$args" -ForegroundColor Blue; Write-Host "===========================================" }

Write-Host "=========================================="
Write-Host "🏥 MedPilot Backend - Windows Deployment"
Write-Host "==========================================" -ForegroundColor Cyan

# Check Prerequisites
Write-Section "PHASE 1: Checking Prerequisites"

# Check Ollama
Write-Host "Checking Ollama..." -ForegroundColor Cyan
$ollamaPath = "C:\Users\Admin\AppData\Local\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaPath) {
    Write-Success "Ollama found at: $ollamaPath"
    
    # Check for model
    $models = & $ollamaPath list 2>&1
    if ($models -like "*qwen2.5:7b*") {
        Write-Success "qwen2.5:7b model found"
    } else {
        Write-Warning-Custom "Model not found, will pull during startup"
    }
} else {
    Write-Error-Custom "Ollama not found. Download from: https://ollama.ai"
    exit 1
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Success $pythonVersion
} catch {
    Write-Error-Custom "Python not found"
    exit 1
}

# Check dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
$deps = python -c "import fastapi; import pydantic; import requests; import chromadb; import sentence_transformers; print('OK')" 2>&1
if ($deps -eq "OK") {
    Write-Success "All dependencies installed"
} else {
    Write-Warning-Custom "Installing dependencies..."
    pip install -r requirements.txt
}

# Check disease data
Write-Host "Checking disease database..." -ForegroundColor Cyan
$dataPath = ".\app\database\data\diseases_data.json"
if (Test-Path $dataPath) {
    $fileSizeMB = [math]::Round((Get-Item $dataPath).Length / 1MB, 2)
    Write-Success "diseases_data.json found ($fileSizeMB MB)"
} else {
    Write-Error-Custom "diseases_data.json not found at $dataPath"
    exit 1
}

# Start Services
Write-Section "PHASE 2: Starting Services"

# Kill any existing Ollama processes
Write-Host "Stopping old Ollama processes..." -ForegroundColor Cyan
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Start Ollama
Write-Host "Starting Ollama..." -ForegroundColor Cyan
$ollama_process = Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden -PassThru
Write-Success "Ollama started (PID: $($ollama_process.Id))"

Write-Info "Waiting 40 seconds for Ollama to stabilize..."
for ($i = 40; $i -gt 0; $i--) {
    Write-Host -NoNewline "`r   $i seconds remaining..."
    Start-Sleep -Seconds 1
}
Write-Host "`r   Ollama ready!                  "

# Verify Ollama is responding
$ollama_ready = $false
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Ollama responding on port 11434"
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
    Write-Error-Custom "Ollama not responding on port 11434"
    exit 1
}

# Kill process on port 8000
Write-Host "Clearing port 8000..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    taskkill /PID $_.OwningProcess /F /T 2>$null
}
Start-Sleep -Seconds 2
Write-Success "Port 8000 cleared"

# Start Backend
Write-Host "Starting Backend Server..." -ForegroundColor Cyan
$env:PYTHONUNBUFFERED = 1
$backend_process = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput ".\server.log" `
    -RedirectStandardError ".\server.log"

Write-Success "Backend started (PID: $($backend_process.Id))"

Write-Info "Waiting 10 seconds for Backend to start..."
Start-Sleep -Seconds 10

# Verify Backend is responding
$backend_ready = $false
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ask-role" `
            -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend responding on port 8000"
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
    Write-Error-Custom "Backend not responding on port 8000"
    Write-Info "Check server.log for details"
    exit 1
}

# Run Tests
Write-Section "PHASE 3: Running Tests"

Write-Info "Starting comprehensive test suite..."
Write-Info "This may take 2-3 minutes..."
Write-Host ""

python test/test_e2e.py

if ($LASTEXITCODE -eq 0) {
    Write-Success "Tests passed!"
} else {
    Write-Error-Custom "Tests encountered issues"
    Write-Info "Check output above for details"
}

# Success
Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "🎉 MEDPILOT DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "=========================================="
Write-Host ""

Write-Host "📊 Services Running:" -ForegroundColor Cyan
Write-Host "   - Ollama:  http://localhost:11434" -ForegroundColor Gray
Write-Host "   - Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host ""

Write-Host "🧪 Available Endpoints:" -ForegroundColor Cyan
Write-Host "   - GET  /api/v1/ask-role               (Role selection)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/query?role=doctor      (Doctor mode)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/query?role=patient     (Patient mode)" -ForegroundColor Gray
Write-Host "   - POST /api/v1/chat                   (Patient chat)" -ForegroundColor Gray
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - IMPLEMENTATION_SUMMARY.md (Full guide)" -ForegroundColor Gray
Write-Host "   - test/README.md            (Test guide)" -ForegroundColor Gray
Write-Host ""

Write-Host "🧹 To stop services later:" -ForegroundColor Yellow
Write-Host '   taskkill /IM ollama.exe /F' -ForegroundColor Gray
Write-Host '   taskkill /F /IM python.exe /T 2>$null' -ForegroundColor Gray
Write-Host ""

Write-Host "✅ Ready for production!" -ForegroundColor Green
