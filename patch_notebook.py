"""
Patch MedPilot_All_In_One_Colab.ipynb:
- Fix ERR_NGROK_334: thêm ngrok.kill() + time.sleep(2) trước khi tạo tunnel mới
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "notebook" / "MedPilot_All_In_One_Colab.ipynb"

# Source mới cho cell tạo ngrok tunnel
NEW_TUNNEL_SOURCE = [
    "# FIX ERR_NGROK_334: Kill ALL existing ngrok sessions trước khi tạo tunnel mới\n",
    "print(\"Creating ngrok tunnel...\")\n",
    "import time\n",
    "\n",
    "try:\n",
    "    # Bước 1: Disconnect từng tunnel đang chạy\n",
    "    for t in ngrok.get_tunnels():\n",
    "        try:\n",
    "            ngrok.disconnect(t.public_url)\n",
    "            print(f\"   Disconnected: {t.public_url}\")\n",
    "        except:\n",
    "            pass\n",
    "\n",
    "    # Bước 2: Kill toàn bộ tiến trình ngrok (tránh ERR_NGROK_334)\n",
    "    ngrok.kill()\n",
    "    time.sleep(2)  # Chờ process thực sự tắt\n",
    "\n",
    "    # Bước 3: Tạo tunnel mới (URL ngẫu nhiên, không conflict URL cũ)\n",
    "    tunnel = ngrok.connect(8000, bind_tls=True)\n",
    "    public_url = tunnel.public_url\n",
    "\n",
    "    print(f\"✅ Tunnel created!\")\n",
    "    print(f\"🌐 URL: {public_url}\")\n",
    "    print()\n",
    "    print(\"📍 Endpoints:\")\n",
    "    print(f\"   Chat:    {public_url}/v1/chat/completions\")\n",
    "    print(f\"   Whisper: {public_url}/v1/audio/transcriptions\")\n",
    "    print(f\"   Extract: {public_url}/v1/extract\")\n",
    "\n",
    "except Exception as e:\n",
    "    print(f\"❌ Tunnel error: {e}\")\n",
    "    raise"
]

def patch():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    patched = 0
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        # Tìm cell tạo ngrok tunnel (chứa ngrok.connect và public_url)
        if "ngrok.connect(8000" in src and "public_url" in src:
            cell["source"] = NEW_TUNNEL_SOURCE
            patched += 1
            print(f"✅ Patched tunnel cell!")

    if patched == 0:
        print("⚠️  Không tìm thấy cell tunnel để patch!")
        return

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print(f"✅ Đã lưu: {NOTEBOOK_PATH}")
    print()
    print("📋 Thay đổi:")
    print("   - Thêm ngrok.kill() trước khi tạo tunnel mới")
    print("   - Thêm time.sleep(2) để process tắt hoàn toàn")
    print("   - Disconnect từng tunnel cũ trước (double safety)")
    print()
    print("🚀 Giờ bạn có thể Run All trong Colab mà không bị ERR_NGROK_334!")

if __name__ == "__main__":
    patch()
