
import requests
import os
import time
import json

def test_full_pipeline():
    url = "http://localhost:8000/api/v1/speech/process-full"
    
    # Create a slightly larger dummy webm file
    dummy_audio = b'\x1a\x45\xdf\xa3\x01\x00\x00\x00\x00\x00\x00\x1f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84\x77\x65\x62\x6d\x42\x87\x81\x02\x42\x85\x81\x02' * 100
    
    files = {
        'file': ('test.webm', dummy_audio, 'audio/webm')
    }
    data = {
        'medical_record': 'Bệnh nhân có tiền sử dị ứng phấn hoa.'
    }
    
    print(f"Testing {url}...")
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        latency = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Latency: {latency:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print("Transcript:", result.get("transcript"))
            print("Structured Data:")
            print(json.dumps(result.get("structured_data"), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Note: Ensure the server is running before executing this
    # uvicorn app.main:app --reload --port 8000
    test_full_pipeline()
