"""
Test E2E - Luong day du tu role selection den response
"""

import requests
import json
import time
import sys
import io

# Fix UTF-8 encoding cho Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
API_BASE = "http://localhost:8000"

def test_role_selection():
    """Test GET /api/v1/ask-role"""
    print("\n" + "="*60)
    print("1️⃣ TEST: Role Selection Endpoint")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/ask-role",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: 200")
            print(f"📋 Message: {result.get('message', '')[:200]}...")
            print(f"🔘 Options: {result.get('options', [])}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_doctor_flow():
    """Test flow: Select Doctor -> Query"""
    print("\n" + "="*60)
    print("2️⃣ TEST: Doctor Flow")
    print("="*60)
    
    # Simulating: User selects "doctor" on frontend
    print("\n▶ User selects: DOCTOR\n")
    
    query = "Bệnh nhân nổi đỏ, ngứa hai bàn tay kéo dài 2 tuần"
    print(f"📋 Query: {query}\n")
    
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
            timeout=120
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: 200")
            print(f"⏱️  Response time: {latency:.2f}s")
            print(f"📊 Retrieved: {result.get('retrieved_chunks', 0)} chunks")
            print(f"📝 Answer preview (first 400 chars):")
            print("-" * 60)
            answer = result.get('answer', '')
            print(answer[:400])
            print("-" * 60)
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_patient_flow():
    """Test flow: Select Patient -> Chat"""
    print("\n" + "="*60)
    print("3️⃣ TEST: Patient Flow")
    print("="*60)
    
    # Simulating: User selects "patient" on frontend
    print("\n▶ User selects: PATIENT\n")
    
    questions = [
        ("Mụn trứng cá là gì?", True),  # (question, expect_dermatology)
        ("Có cách phòng ngừa không?", True),
        ("Mua kem gì để trị?", True),  # Should trigger medication warning
        ("Hôm nay thời tiết thế nào?", False),  # OUT OF SCOPE
    ]
    
    all_success = True
    for question, expect_derm in questions:
        print(f"\n❓ {question}")
        
        payload = {
            "message": question,
            "conversation_id": "test_patient_001"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/api/v1/chat",
                json=payload,
                timeout=120
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('message', '')
                retrieved = result.get('retrieved_chunks', 0)
                
                print(f"✅ Status: 200 | Time: {latency:.2f}s")
                print(f"   Retrieved: {retrieved} chunks")
                print(f"   Answer preview: {answer[:200]}...")
                
                # Check if answer is not empty
                if not answer:
                    print(f"   ⚠️  Empty answer!")
                    all_success = False
            else:
                print(f"❌ Status: {response.status_code}")
                all_success = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_success = False
    
    return all_success


def test_fallback_scenario():
    """Test khi gửi dữ liệu edge cases"""
    print("\n" + "="*60)
    print("4️⃣ TEST: API Robustness")
    print("="*60)
    
    # Send various edge cases
    edge_cases = [
        {"message": "", "description": "Empty message", "expect_status": 422},
        {"message": "   ", "description": "Whitespace only", "expect_status": 422},
        {"message": "a" * 5000, "description": "Very long message", "expect_status": 200},
    ]
    
    all_success = True
    for case in edge_cases:
        print(f"\n📝 Test: {case['description']}")
        
        payload = {
            "message": case['message'],
            "conversation_id": "test_edge_001"
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/chat",
                json=payload,
                timeout=120
            )
            
            expected = case['expect_status']
            if response.status_code == expected:
                print(f"✅ Status: {response.status_code} (expected {expected})")
            else:
                print(f"⚠️  Status: {response.status_code} (expected {expected})")
                all_success = False
                
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    return all_success


def main():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("🚀 END-TO-END TESTS - Complete Flow")
    print("="*70)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/api/v1/ask-role", timeout=5)
        if response.status_code != 200:
            print("❌ API không phản hồi")
            print("   Chạy: python -m uvicorn app.main:app --port 8000")
            return
    except Exception as e:
        print(f"❌ Không kết nối được API: {e}")
        print("   Chạy: python -m uvicorn app.main:app --port 8000")
        return
    
    print("✅ API đang chạy\n")
    
    # Run tests
    result1 = test_role_selection()
    result2 = test_doctor_flow()
    result3 = test_patient_flow()
    result4 = test_fallback_scenario()
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    print(f"1. Role Selection:      {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"2. Doctor Flow:         {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"3. Patient Flow:        {'✅ PASS' if result3 else '❌ FAIL'}")
    print(f"4. API Robustness:      {'✅ PASS' if result4 else '❌ FAIL'}")
    print("="*70)
    
    all_pass = all([result1, result2, result3, result4])
    if all_pass:
        print("\n🎉 ALL TESTS PASSED! System ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Review logs above.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
