"""
Run full test suite: Backend -> E2E -> Interactive
"""

import subprocess
import time
import requests
import sys
import os

def check_backend():
    """Kiem tra backend co chay khong"""
    try:
        r = requests.get("http://localhost:8000/api/v1/ask-role", timeout=5)
        return r.status_code == 200
    except:
        return False

def main():
    print("=" * 60)
    print("MEDPILOT - FULL TEST SUITE")
    print("=" * 60)
    
    # 1. Kiem tra backend
    print("\n[1] Kiem tra backend...")
    if not check_backend():
        print("   Backend chua chay!")
        print("   Chay: python -m uvicorn app.main:app --port 8000")
        return
    
    print("   Backend OK!")
    
    # 2. Chay E2E test
    print("\n[2] Chay E2E Tests...")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            [sys.executable, "test/test_e2e.py"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.getcwd()
        )
        
        # Hien thi ket qua
        lines = result.stdout.split('\n')
        for line in lines:
            if 'PASS' in line or 'FAIL' in line or 'RESULT' in line:
                print(line)
                
        if result.returncode == 0:
            print("\n✅ E2E Tests PASSED!")
        else:
            print("\n⚠️ E2E Tests FAILED!")
            
    except subprocess.TimeoutExpired:
        print("\n⏱️ E2E Test timeout!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("HOAN TAT!")
    print("=" * 60)

if __name__ == "__main__":
    main()