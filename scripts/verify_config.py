
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

print(f"VLLM_API_URL: {settings.VLLM_API_URL}")
print(f"WHISPER_API_URL: {settings.WHISPER_API_URL}")
print(f"EXTRACTION_API_URL: {settings.EXTRACTION_API_URL}")

expected_url = "https://september-unjapanned-detractingly.ngrok-free.dev"
assert expected_url in settings.VLLM_API_URL
assert expected_url in settings.WHISPER_API_URL
assert expected_url in settings.EXTRACTION_API_URL

print("\nVerification successful! All endpoints updated correctly.")
