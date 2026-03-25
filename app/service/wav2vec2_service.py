"""
Wav2Vec2 Vietnamese STT Service
Model: nguyenvulebinh/wav2vec2-base-vietnamese-250h
Audio input: any format (WebM, MP3, WAV) → converted to 16kHz mono
"""

import io
import logging
import tempfile
import os
import time
from typing import Dict

logger = logging.getLogger(__name__)

# Lazy-loaded globals (downloaded on first call ~1GB)
_processor = None
_model = None

MODEL_ID = "nguyenvulebinh/wav2vec2-base-vietnamese-250h"


def _get_model():
    """Load model and processor once and cache them."""
    global _processor, _model
    if _processor is None:
        logger.info(f"[Wav2Vec2] Loading model {MODEL_ID} (first time may take a while)...")
        from transformers import AutoProcessor, AutoModelForCTC
        _processor = AutoProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForCTC.from_pretrained(MODEL_ID)
        logger.info("[Wav2Vec2] Model loaded ✅")
    return _processor, _model


def _convert_to_wav16k(audio_bytes: bytes, mime_type: str) -> bytes:
    """
    Convert any audio format to 16kHz mono WAV bytes.
    Uses pydub (requires ffmpeg on PATH) or torchaudio as fallback.
    """
    # Try pydub first (most reliable for WebM/OGG)
    try:
        from pydub import AudioSegment
        fmt = "webm"
        if "mp3" in mime_type:
            fmt = "mp3"
        elif "wav" in mime_type:
            fmt = "wav"
        elif "ogg" in mime_type:
            fmt = "ogg"
        elif "m4a" in mime_type or "mp4" in mime_type:
            fmt = "mp4"

        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
        audio = audio.set_frame_rate(16000).set_channels(1)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"[Wav2Vec2] pydub failed ({e}), trying torchaudio...")

    # Fallback: torchaudio
    import torchaudio
    import torch

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        waveform, sample_rate = torchaudio.load(tmp_path)
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
        # Convert to mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        buf = io.BytesIO()
        torchaudio.save(buf, waveform, 16000, format="wav")
        return buf.getvalue()
    finally:
        os.unlink(tmp_path)


def transcribe(audio_bytes: bytes, mime_type: str = "audio/webm") -> Dict:
    """
    Transcribe Vietnamese audio using Wav2Vec2.

    Returns:
        {success, transcript, error, latency}
    """
    import torch
    import torchaudio

    start = time.time()
    try:
        logger.info(f"[Wav2Vec2] Converting audio ({len(audio_bytes):,} bytes, {mime_type})...")
        wav_bytes = _convert_to_wav16k(audio_bytes, mime_type)

        logger.info("[Wav2Vec2] Loading waveform for inference...")
        waveform, sample_rate = torchaudio.load(io.BytesIO(wav_bytes))

        # Ensure mono & 16kHz (conversion should already handle this, but double-check)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)

        processor, model = _get_model()

        inputs = processor(
            waveform.squeeze().numpy(),
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )

        logger.info("[Wav2Vec2] Running ASR inference...")
        with torch.no_grad():
            logits = model(**inputs).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcript = processor.batch_decode(predicted_ids)[0].strip()

        latency = time.time() - start
        logger.info(f"[Wav2Vec2] OK ({latency:.1f}s): {transcript[:80]}")
        return {"success": True, "transcript": transcript, "error": None, "latency": latency}

    except Exception as e:
        latency = time.time() - start
        logger.error(f"[Wav2Vec2] Error: {e}")
        return {"success": False, "transcript": "", "error": str(e), "latency": latency}
