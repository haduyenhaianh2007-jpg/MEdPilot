"""
🔍 Debug Script - Test từng endpoint riêng lẻ
Chạy: python test/test_debug.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_patient_chat_debug():
    """Debug Patient Chat endpoint"""
    print("\n" + "="*70)
    print("🔍 DEBUG: Patient Chat Endpoint")
    print("="*70)
    
    query = "Mụn trứng cá là gì?"
    
    payload = {
        "message": query,
        "conversation_id": "debug_001"
    }
    
    print(f"\n📤 Request:")
    print(f"   Endpoint: POST /api/v1/chat")
    print(f"   Message: {query}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload,
            timeout=120
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body:")
        
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check fields
            print(f"\n🔎 Field Check:")
            print(f"   message: {data.get('message', 'MISSING')[:100]}...")
            print(f"   is_dermatology: {data.get('is_dermatology', 'MISSING')}")
            print(f"   has_medication_warning: {data.get('has_medication_warning', 'MISSING')}")
            print(f"   retrieved_chunks: {data.get('retrieved_chunks', 'MISSING')}")
            print(f"   latency: {data.get('latency', 'MISSING')}")
            print(f"   success: {data.get('success', 'MISSING')}")
            
        except:
            print(f"   Raw: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_doctor_query_debug():
    """Debug Doctor Query endpoint"""
    print("\n" + "="*70)
    print("🔍 DEBUG: Doctor Query Endpoint")
    print("="*70)
    
    query = "Bệnh nhân nổi đỏ, ngứa hai bàn tay kéo dài 2 tuần"
    
    payload = {
        "query": query,
        "user_role": "doctor",
        "top_k": 3
    }
    
    print(f"\n📤 Request:")
    print(f"   Endpoint: POST /api/v1/query")
    print(f"   Query: {query}")
    print(f"   Role: doctor")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            json=payload,
            timeout=120
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body:")
        
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check fields
            print(f"\n🔎 Field Check:")
            print(f"   query: {data.get('query', 'MISSING')}")
            print(f"   answer: {data.get('answer', 'MISSING')[:100]}...")
            print(f"   retrieved_chunks: {data.get('retrieved_chunks', 'MISSING')}")
            print(f"   latency: {data.get('latency', 'MISSING')}")
            print(f"   success: {data.get('success', 'MISSING')}")
            
        except:
            print(f"   Raw: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


def check_server():
    """Check if server is running"""
    print("\n" + "="*70)
    print("🔍 DEBUG: Server Health Check")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ask-role",
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"\n✅ Server is running at {BASE_URL}")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"\n⚠️  Server returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running: python -m app.main")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         🔍 Debug Script - Test Endpoints Individually              ║
║                                                                    ║
║  This script tests each endpoint and shows full response details  ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check server first
    if not check_server():
        print("\n⛔ Cannot proceed - server is not running!")
        return
    
    # Test endpoints
    test_patient_chat_debug()
    test_doctor_query_debug()
    
    print("\n" + "="*70)
    print("✅ Debug complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
