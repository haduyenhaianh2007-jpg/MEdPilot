"""
Test script cho chế độ BÁC SĨ
Upload file JSON và nhận gợi ý chẩn đoán chi tiết
"""

import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
TEST_JSON_PATH = Path(__file__).parent.parent / "app" / "test.json"

def load_test_data():
    """Load test.json"""
    try:
        with open(TEST_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Lỗi load file: {e}")
        return None


def test_doctor_mode_single_query():
    """Test doctor mode - single query"""
    print("\n" + "="*60)
    print("🩺 TEST: Doctor Mode - Single Query")
    print("="*60)
    
    test_data = load_test_data()
    if not test_data:
        return False
    
    # Extract clinical summary as query
    query = test_data.get("structured_summary", {}).get("one_liner", "")
    if not query:
        query = test_data.get("chief_complaint", "Nổi đỏ, ngứa")
    
    print(f"\n📋 Query: {query[:100]}...")
    
    payload = {
        "query": query,
        "user_role": "doctor",
        "top_k": 5,
        "max_tokens": 2000
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/v1/query",
            json=payload,
            timeout=60
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Status: 200")
            print(f"⏱️  Latency: {latency:.2f}s")
            print(f"📊 Retrieved chunks: {result.get('retrieved_chunks', 0)}")
            print(f"\n📝 Answer (first 500 chars):")
            print("-" * 60)
            answer = result.get('answer', '').replace('\n', '\n')
            print(answer[:500])
            print("-" * 60)
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout after 60s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_doctor_mode_multi_turn():
    """Test doctor mode - multi-turn conversation"""
    print("\n" + "="*60)
    print("🩺 TEST: Doctor Mode - Multi-Turn Follow-up")
    print("="*60)
    
    test_data = load_test_data()
    if not test_data:
        return False
    
    # First query
    query1 = test_data.get("structured_summary", {}).get("one_liner", "")
    if not query1:
        query1 = "Bệnh nhân nổi đỏ, ngứa ở hai bàn tay kéo dài 2 tuần"
    
    print(f"\n📋 Query 1: {query1[:80]}...")
    
    payload1 = {
        "query": query1,
        "user_role": "doctor",
        "top_k": 5
    }
    
    try:
        response1 = requests.post(
            f"{API_BASE}/api/v1/query",
            json=payload1,
            timeout=60
        )
        
        if response1.status_code == 200:
            print(f"✅ Query 1 success")
            
            # Follow-up query
            query2 = "Cách phân biệt với contact dermatitis và atopic dermatitis?"
            print(f"\n📋 Query 2 (Follow-up): {query2[:80]}...")
            
            payload2 = {
                "query": query2,
                "user_role": "doctor",
                "top_k": 5
            }
            
            response2 = requests.post(
                f"{API_BASE}/api/v1/query",
                json=payload2,
                timeout=60
            )
            
            if response2.status_code == 200:
                print(f"✅ Query 2 success")
                result2 = response2.json()
                print(f"📊 Retrieved: {result2.get('retrieved_chunks', 0)} chunks")
                return True
            else:
                print(f"❌ Query 2 failed: {response2.status_code}")
                return False
        else:
            print(f"❌ Query 1 failed: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🩺 DOCTOR MODE TESTS")
    print("="*60)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/api/v1/ask-role", timeout=5)
        if response.status_code != 200:
            print("❌ API không phản hồi. Chạy: python -m uvicorn app.main:app --port 8000")
            return
    except Exception as e:
        print(f"❌ Không kết nối được API: {e}")
        print("   Chạy: python -m uvicorn app.main:app --port 8000")
        return
    
    print("✅ API đang chạy\n")
    
    # Run tests
    result1 = test_doctor_mode_single_query()
    result2 = test_doctor_mode_multi_turn()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Single Query: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Multi-Turn:    {'✅ PASS' if result2 else '❌ FAIL'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
