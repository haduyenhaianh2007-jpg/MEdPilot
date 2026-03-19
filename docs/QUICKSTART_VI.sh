#!/bin/bash
# 🚀 MEDPILOT - Triển Khai Tự Động cho Linux/Mac
# Script này sẽ cài đặt, kiểm tra và chạy toàn bộ hệ thống

echo "=========================================="
echo "🏥 MedPilot Backend - Triển Khai Nhanh"
echo "=========================================="
echo ""

# Định nghĩa màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Không có màu

# ============================================
# GIAI ĐOẠN 1: Kiểm Tra Yêu Cầu
# ============================================
echo -e "${BLUE}GIAI ĐOẠN 1: Kiểm Tra Các Yêu Cầu Trước${NC}"
echo "=========================================="
echo ""

# Kiểm Tra Ollama
echo -e "${BLUE}Đang kiểm tra Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama không được tìm thấy${NC}"
    echo "   Tải từ: https://ollama.ai"
    exit 1
fi
echo -e "${GREEN}✅ Ollama được tìm thấy${NC}"

# Kiểm Tra Model
if ollama list | grep -q "qwen2.5:7b"; then
    echo -e "${GREEN}✅ Model qwen2.5:7b được tìm thấy${NC}"
else
    echo -e "${YELLOW}⚠️  Model không được tìm thấy, đang pull...${NC}"
    ollama pull qwen2.5:7b
fi

# Kiểm Tra Python
echo ""
echo -e "${BLUE}Đang kiểm tra Python...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python không được tìm thấy${NC}"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# Kiểm Tra Phụ Thuộc
echo ""
echo -e "${BLUE}Đang kiểm tra các gói Python...${NC}"
python -c "import fastapi; import pydantic; import requests; import chromadb; import sentence_transformers" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Các gói phụ thuộc không đầy đủ, đang cài đặt...${NC}"
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ Tất cả gói phụ thuộc đã được cài đặt${NC}"
fi

# Kiểm Tra Dữ Liệu Bệnh Lý
echo ""
echo -e "${BLUE}Đang kiểm tra kho bệnh lý...${NC}"
if [ -f "app/database/data/diseases_data.json" ]; then
    FILE_SIZE=$(du -h app/database/data/diseases_data.json | cut -f1)
    echo -e "${GREEN}✅ diseases_data.json được tìm thấy ($FILE_SIZE)${NC}"
else
    echo -e "${RED}❌ diseases_data.json không được tìm thấy${NC}"
    exit 1
fi

# ============================================
# GIAI ĐOẠN 2: Khởi Động Dịch Vụ
# ============================================
echo ""
echo -e "${BLUE}GIAI ĐOẠN 2: Khởi Động Các Dịch Vụ${NC}"
echo "=========================================="
echo ""

# Dừng Ollama Cũ
echo -e "${BLUE}Đang dừng các process Ollama cũ...${NC}"
pkill -f "ollama serve" || true
sleep 2

# Khởi Động Ollama
echo -e "${BLUE}Đang khởi động Ollama...${NC}"
ollama serve > ollama.log 2>&1 &
OLLAMA_PID=$!
echo -e "${GREEN}✅ Ollama đã khởi động (PID: $OLLAMA_PID)${NC}"

# Chờ Ollama Ổn Định
echo -e "${BLUE}Đang chờ 40 giây để Ollama ổn định...${NC}"
for i in {40..1}; do
    printf "\r   %d giây còn lại...     " "$i"
    sleep 1
done
echo -e "\n${GREEN}✅ Ollama sẵn sàng!${NC}"

# Kiểm Tra Ollama Phản Hồi
echo -e "${BLUE}Kiểm tra Ollama phản hồi...${NC}"
for attempt in {1..5}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama đang phản hồi trên port 11434${NC}"
        break
    fi
    if [ $attempt -lt 5 ]; then
        sleep 5
    fi
done

# Kiểm Tra Port 8000
echo -e "${BLUE}Đang kiểm tra port 8000...${NC}"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 đang được sử dụng, dừng process...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo -e "${GREEN}✅ Port 8000 sẵn sàng${NC}"

# Khởi Động Backend
echo ""
echo -e "${BLUE}Đang khởi động Backend Server...${NC}"
export PYTHONUNBUFFERED=1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend đã khởi động (PID: $BACKEND_PID)${NC}"

echo -e "${BLUE}Đang chờ 10 giây để Backend khởi động...${NC}"
sleep 10

# Kiểm Tra Backend Phản Hồi
echo -e "${BLUE}Kiểm tra Backend phản hồi...${NC}"
for attempt in {1..5}; do
    if curl -s http://localhost:8000/api/v1/ask-role > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend đang phản hồi trên port 8000${NC}"
        break
    fi
    if [ $attempt -lt 5 ]; then
        sleep 3
    fi
done

# ============================================
# GIAI ĐOẠN 3: Chạy Test
# ============================================
echo ""
echo -e "${BLUE}GIAI ĐOẠN 3: Chạy Bộ Test Toàn Diện${NC}"
echo "=========================================="
echo ""

echo -e "${BLUE}Đang khởi động bộ test toàn diện...${NC}"
echo -e "${BLUE}Điều này có thể mất 2-3 phút...${NC}"
echo ""

python test/test_e2e.py

if [ $? -eq 0 ]; then
    TEST_RESULT="${GREEN}✅ Test đã thành công!${NC}"
else
    TEST_RESULT="${RED}❌ Test gặp vấn đề${NC}"
fi

# ============================================
# HOÀN THÀNH
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 TRIỂN KHAI MEDPILOT THÀNH CÔNG!${NC}"
echo "=========================================="
echo ""

echo -e "${BLUE}📊 Các Dịch Vụ Đang Chạy:${NC}"
echo "   - Ollama:  http://localhost:11434"
echo "   - Backend: http://localhost:8000"
echo ""

echo -e "${BLUE}🧪 Các Endpoint Có Sẵn:${NC}"
echo "   - GET  /api/v1/ask-role              (Lựa chọn vai trò)"
echo "   - POST /api/v1/query?role=doctor     (Chế độ bác sĩ)"
echo "   - POST /api/v1/query?role=patient    (Chế độ bệnh nhân)"
echo "   - POST /api/v1/chat                  (Hội thoại bệnh nhân)"
echo ""

echo -e "${BLUE}📚 Tài Liệu:${NC}"
echo "   - IMPLEMENTATION_SUMMARY_VI.md (Hướng dẫn đầy đủ)"
echo "   - FINAL_CHECKLIST_VI.md        (Danh sách kiểm tra)"
echo "   - test/README.md               (Hướng dẫn test)"
echo ""

echo -e "${YELLOW}🧹 Để dừng dịch vụ sau này:${NC}"
echo "   kill $OLLAMA_PID"
echo "   kill $BACKEND_PID"
echo ""

echo -e "${GREEN}✅ Sẵn sàng cho sản xuất!${NC}"
echo ""
