"""
🔍 Check vLLM / Ollama Status trước khi chạy test
Chạy: python test/check_vllm_status.py
"""

import requests
import time
import sys

# Configuration
OLLAMA_URL = "http://localhost:11434"
API_BASE = "http://localhost:8000"
MODEL_NAME = "qwen2.5"

def check_ollama_health():
    """Check if Ollama server is running"""
    print("\n" + "="*70)
    print("🔍 STEP 1: Check Ollama / vLLM Server")
    print("="*70)
    
    try:
        # Try to list models
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama server is running at {OLLAMA_URL}")
            print(f"📦 Available models: {len(models)}")
            
            for model in models:
                model_name = model.get("name", "unknown")
                print(f"   • {model_name}")
            
            # Check if qwen2.5 is loaded
            qwen_found = any(MODEL_NAME in m.get("name", "") for m in models)
            if qwen_found:
                print(f"\n✅ {MODEL_NAME} model is available!")
                return True
            else:
                print(f"\n⚠️  {MODEL_NAME} model not found!")
                print(f"   Need to pull: ollama pull qwen2.5")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"   Make sure Ollama is running:")
        print(f"   $ ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def warmup_model():
    """Send a warmup request to vLLM to load model in memory"""
    print("\n" + "="*70)
    print("🚀 STEP 2: Warmup Model (First request is slow - prepare cache)")
    print("="*70)
    
    try:
        print(f"\n📝 Sending warmup request to {MODEL_NAME}...")
        print(f"   (This may take 30-60s first time)")
        
        start_time = time.time()
        
        # Send simple test query
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": "Hello, who are you?",
                "stream": False,
            },
            timeout=120
        )
        
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Warmup successful!")
            print(f"   Response time: {latency:.2f}s")
            print(f"   Model is now loaded in cache ⚡")
            return True
        else:
            print(f"❌ Warmup failed: Status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  WARNING: Warmup timed out (>120s)")
        print(f"   Model might be very slow or not loading")
        return False
    except Exception as e:
        print(f"❌ Warmup error: {e}")
        return False


def check_fastapi_health():
    """Check if FastAPI backend is running"""
    print("\n" + "="*70)
    print("🔍 STEP 3: Check FastAPI Backend")
    print("="*70)
    
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/ask-role",
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"\n✅ FastAPI backend is running at {API_BASE}")
            print(f"   /api/v1/ask-role endpoint is responding")
            return True
        else:
            print(f"❌ FastAPI returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to FastAPI at {API_BASE}")
        print(f"   Make sure server is running:")
        print(f"   $ python -m app.main")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all checks"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     🚀 vLLM / Ollama Status Check - Pre-Test Validation            ║
║                                                                    ║
║  This checks if your backend is ready for E2E tests               ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Check 1: Ollama health
    ollama_ok = check_ollama_health()
    results.append(("Ollama Server", ollama_ok))
    
    if not ollama_ok:
        print("\n⛔ Cannot continue - Ollama is not running!")
        print("   Start Ollama first: ollama serve")
        sys.exit(1)
    
    # Check 2: Warmup model
    warmup_ok = warmup_model()
    results.append(("Model Warmup", warmup_ok))
    
    # Check 3: FastAPI
    fastapi_ok = check_fastapi_health()
    results.append(("FastAPI Backend", fastapi_ok))
    
    # Summary
    print("\n" + "="*70)
    print("📊 SYSTEM STATUS SUMMARY")
    print("="*70)
    
    all_ok = True
    for name, status in results:
        status_str = "✅ OK" if status else "❌ FAILED"
        print(f"  {name}: {status_str}")
        if not status:
            all_ok = False
    
    print("\n" + "="*70)
    
    if all_ok:
        print("\n🎉 All checks passed! System is ready for testing!")
        print("\n▶ Next step: python test/test_e2e.py\n")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the errors above.")
        print("   Then run this check again.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
