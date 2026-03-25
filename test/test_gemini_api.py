"""
Test script - Kiem tra Google Gemini API Key va cac models co san
"""

import requests
import json
import os

API_KEY = os.getenv("GOOGLE_API_KEY") or "AIzaSyDc3Q8OSug9HlhZBTybad6K0alikggOFDg"

def test_api_key_and_list_models(api_key: str):
    """Test API key va liet ke cac models co san"""
    
    print("=" * 60)
    print("TESTING GOOGLE GEMINI API")
    print("=" * 60)
    
    print("\n[1] Liet ke models...")
    print("-" * 40)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            print(f"[OK] API Key hop le!")
            print(f"[INFO] Tong so models: {len(models)}\n")
            
            flash_models = []
            pro_models = []
            other_models = []
            
            for model in models:
                name = model.get("name", "")
                
                if "flash" in name.lower():
                    flash_models.append(name)
                elif "pro" in name.lower():
                    pro_models.append(name)
                else:
                    other_models.append(name)
            
            print("=== GEMINI FLASH (Nhanh, re, phu hop RAG):")
            for m in flash_models:
                print(f"   - {m}")
            
            print("\n=== GEMINI PRO (Manh, phan tich phuc tap):")
            for m in pro_models:
                print(f"   - {m}")
            
            print("\n=== OTHER MODELS:")
            for m in other_models:
                print(f"   - {m}")
            
            return models
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return None


def test_chat_completion(api_key: str, model: str = "gemini-1.5-flash"):
    """Test gui chat request"""
    
    print("\n" + "=" * 60)
    print(f"[2] Test chat voi model '{model}'")
    print("-" * 40)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Xin chao, ban la ai?"
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100
        }
    }
    
    try:
        print("Dang gui request...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            print(f"[OK] Thanh cong!")
            print(f"\n--- Response ---")
            print(answer)
            print("-" * 40)
            return True
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return False


def main():
    """Main test"""
    
    api_key = API_KEY
    
    if not api_key:
        print("[ERROR] Khong tim thay GOOGLE_API_KEY")
        return
    
    print(f"[OK] API Key: {api_key[:20]}...{api_key[-4:]}")
    
    models = test_api_key_and_list_models(api_key)
    
    if models:
        test_chat_completion(api_key, "gemini-1.5-flash")
        
        print("\n" + "=" * 60)
        print("[OK] KET LUAN")
        print("=" * 60)
        print("API Key hoat dong tot!")
        print("\n[INFO] Model khuyen nghi cho RAG:")
        print("   - gemini-1.5-flash (nhanh, re)")
        print("   - gemini-1.5-pro (manh hon)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
