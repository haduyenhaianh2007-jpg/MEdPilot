import requests
import json

def test_extract():
    url = "http://localhost:8000/api/v1/speech/extract"
    payload = {
        "transcript": "Chào bác sĩ, tôi bị ngứa ở cánh tay trái khoảng 3 ngày nay rồi. Vùng da đó nổi nốt đỏ và hơi khô. Tôi chưa dùng thuốc gì cả.",
        "medical_record": ""
    }
    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true"
    }

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Extraction Result:")
            print(json.dumps(result.get("structured_data", {}), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_extract()
