"""
Test script cho chế độ BỆNH NHÂN
Hỏi đáp liên tục về da liễu, cảnh báo mua thuốc, từ chối ngoài lĩnh vực
"""

import requests
import json
import time
import uuid

# Configuration
API_BASE = "http://localhost:8000"

def test_patient_dermatology_questions():
    """Test câu hỏi về da liễu"""
    print("\n" + "="*60)
    print("🧑‍🤝‍🧑 TEST: Patient Mode - Dermatology Q&A")
    print("="*60)
    
    conversation_id = str(uuid.uuid4())
    
    questions = [
        "Mụn trứng cá là gì? Cách phòng ngừa?",
        "Làm thế nào để phân biệt mụn và nổi mẩn đỏ?",
        "Chàm da là bệnh gì? Có nguy hiểm không?",
        "Nên dùng loại sữa rửa mặt nào cho da nhạy cảm?"
    ]
    
    print(f"\n📝 Conversation ID: {conversation_id}\n")
    
    all_success = True
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Question {i}: {question}")
        
        payload = {
            "message": question,
            "conversation_id": conversation_id,
            "top_k": 3
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/api/v1/query?role=patient",
                json=payload,
                timeout=60
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                is_derm = result.get('is_dermatology', False)
                print(f"✅ Status: 200 | Dermatology: {is_derm} | Latency: {latency:.2f}s")
                print(f"📝 Answer (first 300 chars):")
                print("-" * 60)
                answer = result.get('answer', '')[:300]
                print(answer)
                print("-" * 60)
            else:
                print(f"❌ Status: {response.status_code}")
                all_success = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_success = False
    
    return all_success


def test_patient_medication_warning():
    """Test cảnh báo khi hỏi mua thuốc"""
    print("\n" + "="*60)
    print("⚠️  TEST: Patient Mode - Medication Warning")
    print("="*60)
    
    conversation_id = str(uuid.uuid4())
    
    medication_questions = [
        "Mụn trứng cá nên dùng thuốc gì?",
        "Có thuốc nào tốt để chữa chàm không?",
        "Kem này ở đâu mua?",
        "Nên lấy thuốc nào từ nhà thuốc?"
    ]
    
    print(f"\n📝 Conversation ID: {conversation_id}\n")
    
    all_success = True
    for i, question in enumerate(medication_questions, 1):
        print(f"\n⚠️  Question {i}: {question}")
        
        payload = {
            "message": question,
            "conversation_id": conversation_id
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/query?role=patient",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                has_warning = result.get('has_medication_warning', False)
                print(f"✅ Status: 200 | Med Warning: {has_warning}")
                
                if has_warning:
                    print("📋 Expected: CẢNH BÁO xuất hiện")
                    print("-" * 60)
                    print(result.get('answer', '')[:400])
                    print("-" * 60)
                else:
                    print("⚠️  Expect medication warning to be TRUE")
            else:
                print(f"❌ Status: {response.status_code}")
                all_success = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_success = False
    
    return all_success


def test_patient_nonderm_rejection():
    """Test từ chối câu hỏi ngoài da liễu"""
    print("\n" + "="*60)
    print("🚫 TEST: Patient Mode - Non-Dermatology Rejection")
    print("="*60)
    
    conversation_id = str(uuid.uuid4())
    
    non_derm_questions = [
        "Tôi bị đau bụng, phải làm sao?",
        "2 + 2 bằng mấy?",
        "Cách chữa trị tiểu đường?",
        "Tôi bị ho, phải uống thuốc gì?"
    ]
    
    print(f"\n📝 Conversation ID: {conversation_id}\n")
    
    all_success = True
    for i, question in enumerate(non_derm_questions, 1):
        print(f"\n❓ Question {i}: {question}")
        
        payload = {
            "message": question,
            "conversation_id": conversation_id
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/query?role=patient",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                is_derm = result.get('is_dermatology', False)
                print(f"✅ Status: 200 | Is Dermatology: {is_derm}")
                
                if not is_derm:
                    print("✅ Correctly identified as NON-DERMATOLOGY")
                    # Should see rejection message
                    answer = result.get('answer', '').lower()
                    if "không thể trả lời" in answer or "ngoài" in answer:
                        print("✅ Rejection message present")
                else:
                    print("⚠️  Should NOT be dermatology")
                
                print("-" * 60)
                print(result.get('answer', '')[:300])
                print("-" * 60)
            else:
                print(f"❌ Status: {response.status_code}")
                all_success = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_success = False
    
    return all_success


def test_patient_conversation_history():
    """Test lịch sử chat được lưu"""
    print("\n" + "="*60)
    print("💬 TEST: Patient Mode - Conversation History")
    print("="*60)
    
    conversation_id = str(uuid.uuid4())
    
    questions = [
        "Mụn trứng cá là bệnh gì?",
        "Phòng ngừa làm sao?",
        "Nên gặp bác sĩ nào?"
    ]
    
    print(f"\n📝 Conversation ID: {conversation_id}")
    print("Kiểm tra lịch sử được lưu (same conversation_id)\n")
    
    all_success = True
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Message {i}: {question}")
        
        payload = {
            "message": question,
            "conversation_id": conversation_id
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/query?role=patient",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                returned_conv_id = result.get('conversation_id')
                print(f"✅ Status: 200")
                print(f"📝 Returned Conv ID matches: {returned_conv_id == conversation_id}")
                
            else:
                print(f"❌ Status: {response.status_code}")
                all_success = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_success = False
    
    return all_success


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧑‍🤝‍🧑 PATIENT MODE TESTS")
    print("="*60)
    
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
    result1 = test_patient_dermatology_questions()
    result2 = test_patient_medication_warning()
    result3 = test_patient_nonderm_rejection()
    result4 = test_patient_conversation_history()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Dermatology Q&A:        {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Medication Warning:     {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"Non-Derm Rejection:     {'✅ PASS' if result3 else '❌ FAIL'}")
    print(f"Conversation History:   {'✅ PASS' if result4 else '❌ FAIL'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
