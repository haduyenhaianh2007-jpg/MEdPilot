from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_speech_extract():
    print("Testing /api/v1/speech/extract...")
    payload = {
        "transcript": "Chào bác sĩ, tôi bị ngứa ở cánh tay trái khoảng 3 ngày nay rồi. Vùng da đó nổi nốt đỏ và hơi khô.",
        "medical_record": ""
    }
    response = client.post("/api/v1/speech/extract", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Data extracted.")
        print(json.dumps(response.json().get("structured_data", {}), indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")

def test_chat():
    print("\nTesting /api/v1/chat...")
    payload = {
        "message": "Bệnh chàm là gì?",
    }
    response = client.post("/api/v1/chat", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Chat response received.")
        print(response.json().get("message")[:100] + "...")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_speech_extract()
    test_chat()
    # Note: transcribe requires audio file, skipping in this quick check
