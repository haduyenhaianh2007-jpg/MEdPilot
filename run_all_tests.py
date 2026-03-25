"""
Run all tests lien tuc: Backend -> E2E -> Interactive
"""

import subprocess
import time
import sys
import os

def run_command(cmd, name, timeout=None):
    """Chay command va hien thi output"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {name}")
    print(f"Command: {cmd}")
    print(f"{'='*60}\n")
    
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        
        for line in process.stdout:
            try:
                print(line.decode('utf-8', errors='replace').rstrip())
            except:
                pass
        
        process.wait(timeout=timeout)
        return process.returncode
        
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {name} took too long")
        process.kill()
        return -1
    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] {name}")
        process.kill()
        return -2

def main():
    print("=" * 60)
    print("MEDPILOT - FULL TEST SUITE")
    print("=" * 60)
    
    # 1. Start backend
    print("\n[1] Starting Backend...")
    backend_proc = subprocess.Popen(
        "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    time.sleep(15)
    
    # Check if backend started
    import requests
    try:
        r = requests.get("http://localhost:8000/api/v1/ask-role", timeout=5)
        if r.status_code == 200:
            print("[OK] Backend is running!\n")
        else:
            print(f"[WARN] Backend returned status {r.status_code}\n")
    except Exception as e:
        print(f"[WARN] Could not verify backend: {e}\n")
    
    # 2. Run E2E tests
    print("\n[2] Running E2E Tests...")
    e2e_result = run_command(
        "python test/test_e2e.py",
        "E2E TEST",
        timeout=600
    )
    
    # 3. Ask to run interactive
    print("\n" + "=" * 60)
    print("[3] Interactive Test")
    print("=" * 60)
    print("Chay interactive test? (y/n): ", end="")
    
    try:
        choice = input().strip().lower()
    except:
        choice = "n"
    
    if choice == "y":
        run_command(
            "python test/test_interactive.py --auto",
            "INTERACTIVE TEST",
            timeout=300
        )
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleaning up...")
    backend_proc.terminate()
    print("Done!")

if __name__ == "__main__":
    main()
