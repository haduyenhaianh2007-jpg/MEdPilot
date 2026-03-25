import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def test_model(model_name):
    print(f"Testing model: {model_name}...")
    url = f"{BASE_URL}/{model_name}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, how are you?"}]}]
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            # print(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_model("gemini-2.5-flash") # The one in code
    test_model("gemini-2.0-flash") # The one in STT code
    test_model("gemini-1.5-flash") # Stable fallback
    test_model("gemini-2.0-flash-exp") # Another common one
