"""
🧪 Interactive Test Script - Test Role Selection & Both Modes
Chạy: python test/test_interactive.py
"""

import requests
import json
from typing import Optional

# API Base URL
BASE_URL = "http://localhost:8000"

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_ask_role():
    """Test 1: Hỏi role"""
    print_header("Test 1️⃣  - HỎI ROLE (Ask Role)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ask-role")
        response.raise_for_status()
        
        data = response.json()
        print("✅ Response Status:", response.status_code)
        print("\n📋 Message:")
        print(data.get("message", ""))
        print("\n📌 Available Options:")
        for opt in data.get("options", []):
            print(f"  → {opt}")
        
        return True
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server!")
        print("   Make sure FastAPI server is running: python -m app.main")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_doctor_mode(query: str = "Bệnh nhân bị mụn đỏ sưng tấy trên mặt"):
    """Test 2: Doctor Mode"""
    print_header("Test 2️⃣  - DOCTOR MODE (Chế độ Bác Sĩ)")
    
    try:
        payload = {
            "query": query,
            "user_role": "doctor",
            "top_k": 5
        }
        
        print(f"📤 Request:")
        print(f"   Query: {query}")
        print(f"   Role: doctor")
        print(f"   Mode: Diagnostic support (detailed, technical)\n")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Response Status: {response.status_code}")
        print(f"\n🩺 Medical Diagnostic Response:")
        print("-" * 70)
        print(data.get("answer", "No answer"))
        print("-" * 70)
        print(f"\n📊 Metadata:")
        print(f"   Retrieved chunks: {data.get('retrieved_chunks', 0)}")
        print(f"   Latency: {data.get('latency', 0):.2f}s")
        print(f"   Success: {data.get('success', False)}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_patient_mode(query: str = "Mụn trên mặt là bệnh gì? Làm sao để ngừa?"):
    """Test 3: Patient Chat Mode"""
    print_header("Test 3️⃣  - PATIENT MODE (Chế độ Bệnh Nhân)")
    
    try:
        payload = {
            "message": query,
            "conversation_id": None,
            "top_k": 3
        }
        
        print(f"📤 Request:")
        print(f"   Query: {query}")
        print(f"   Role: patient")
        print(f"   Mode: Educational Q&A (simple, no diagnosis)\n")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Response Status: {response.status_code}")
        print(f"\n💬 Educational Response:")
        print("-" * 70)
        print(data.get("answer", "No answer"))
        print("-" * 70)
        print(f"\n📊 Metadata:")
        print(f"   Retrieved chunks: {data.get('retrieved_chunks', 0)}")
        print(f"   Latency: {data.get('latency', 0):.2f}s")
        print(f"   Success: {data.get('success', False)}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_medication_warning():
    """Test 4: Medication Purchase Warning"""
    print_header("Test 4️⃣  - MEDICATION WARNING (Cảnh báo Mua Thuốc)")
    
    try:
        query = "Mình có mụn, bây giờ tự mua kem nào là được không? Hiệu nào bán kem trị mụn?"
        
        payload = {
            "message": query,
            "conversation_id": None,
            "top_k": 3
        }
        
        print(f"📤 Request (Medication-related query):")
        print(f"   Query: {query}")
        print(f"   Expected: Should block or warn about self-medication\n")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Response Status: {response.status_code}")
        print(f"\n⚠️  Response (Should include warning):")
        print("-" * 70)
        print(data.get("answer", "No answer"))
        print("-" * 70)
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_non_dermatology():
    """Test 5: Out-of-scope Question"""
    print_header("Test 5️⃣  - OUT-OF-SCOPE (Câu hỏi Ngoài Phạm Vi)")
    
    try:
        query = "Làm sao để chữa bệnh tim? Em chảy máu mũi phải làm gì?"
        
        payload = {
            "message": query,
            "conversation_id": None,
            "top_k": 3
        }
        
        print(f"📤 Request (Non-dermatology query):")
        print(f"   Query: {query}")
        print(f"   Expected: Should refuse with polite message\n")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Response Status: {response.status_code}")
        print(f"\n🚫 Response (Should refuse):")
        print("-" * 70)
        print(data.get("answer", "No answer"))
        print("-" * 70)
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def interactive_mode():
    """Interactive continuous Q&A"""
    print_header("🎯 INTERACTIVE MODE - Continuous Q&A")
    print("💡 Tip: Type 'doctor' to switch to doctor mode, 'exit' to quit\n")
    
    mode = "patient"
    session_id = None
    
    while True:
        try:
            if mode == "patient":
                user_input = input("🧑‍🤝‍🧑 [PATIENT] Your question: ").strip()
            else:
                user_input = input("👨‍⚕️  [DOCTOR] Your query: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 Thanks for using MedPilot!")
                break
            
            if user_input.lower() == "doctor":
                mode = "doctor"
                print("✅ Switched to DOCTOR mode")
                continue
            
            if user_input.lower() == "patient":
                mode = "patient"
                print("✅ Switched to PATIENT mode")
                continue
            
            # Send request
            if mode == "doctor":
                payload = {
                    "query": user_input,
                    "user_role": "doctor"
                }
                endpoint = "/api/v1/query"
            else:
                payload = {
                    "message": user_input,
                    "conversation_id": None,
                    "top_k": 3
                }
                endpoint = "/api/v1/chat"
            
            # Ghi request thực tế vào logs/request.log
            request_log = {
                "query": user_input,
                "mode": mode,
                "payload": payload
            }
            with open('logs/request.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(request_log, ensure_ascii=False) + '\n')
            
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"\n✅ Response:\n")
            print(data.get("answer", "No answer"))
            print(f"\n⏱️  Latency: {data.get('latency', 0):.2f}s\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted!")
            break
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}\n")

def main():
    """Main test runner"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         🏥 MedPilot RAG Backend - Interactive Test Suite           ║
║                                                                    ║
║  Chế độ Bác Sĩ: Hỗ trợ chẩn đoán chi tiết                         ║
║  Chế độ Bệnh Nhân: Hỏi-đáp giáo dục + Cảnh báo tự mua thuốc       ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print("📝 Chọn mode test:")
    print("  1. Chạy tất cả tests tự động")
    print("  2. Interactive (hỏi-đáp liên tục)")
    print("  3. Chỉ test Role Selection")
    
    # Auto run mode 1 if no input
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        choice = "1"
    else:
        try:
            choice = input("\n👉 Chọn (1/2/3): ").strip()
        except EOFError:
            choice = "1"
            print("Running auto mode...")
    
    if choice == "1":
        # Run all tests
        results = []
        
        results.append(("Ask Role", test_ask_role()))
        if results[-1][1]:  # If role selection works
            results.append(("Doctor Mode", test_doctor_mode()))
            results.append(("Patient Mode", test_patient_mode()))
            results.append(("Medication Warning", test_medication_warning()))
            results.append(("Out-of-scope", test_non_dermatology()))
        
        # Summary
        print_header("📊 TEST SUMMARY")
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {name}: {status}")
        
        passed_count = sum(1 for _, p in results if p)
        print(f"\n📈 Total: {passed_count}/{len(results)} tests passed\n")
        
    elif choice == "2":
        interactive_mode()
        
    elif choice == "3":
        test_ask_role()
    
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
