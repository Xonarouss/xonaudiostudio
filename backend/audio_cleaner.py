import os
import tempfile
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from pathlib import Path
from typing import Optional, Tuple

def trim_silence(
    audio: np.ndarray,
    sr: int,
    threshold_db: float = -42.0,
    pad_ms: int = 120,
) -> np.ndarray:
    """
    Trims leading and trailing silence from audio using frame-based RMS energy detection.
    pad_ms preserves natural onset and tail so consonants are not truncated.
    """
    if len(audio) == 0:
        return audio

    # For multi-channel, use max across channels to find voice activity
    if audio.ndim == 1:
        mono = np.abs(audio)
    else:
        mono = np.max(np.abs(audio), axis=-1)

    peak = np.max(mono)
    if peak < 1e-5:
        # Audio is completely silent, return as is
        return audio

    # Calculate frame RMS in 20ms windows with 10ms hops
    frame_length = max(1, int(sr * 0.020))
    hop_length = max(1, int(sr * 0.010))
    pad_samples = int(sr * (pad_ms / 1000.0))

    threshold_linear = peak * (10 ** (threshold_db / 20.0))

    num_frames = (len(mono) - frame_length) // hop_length + 1
    if num_frames <= 0:
        return audio

    # Find first and last frames above threshold
    start_idx = 0
    end_idx = len(audio)

    # Search from start
    for i in range(num_frames):
        chunk = mono[i * hop_length : i * hop_length + frame_length]
        rms = np.sqrt(np.mean(chunk ** 2) + 1e-12)
        if rms >= threshold_linear:
            start_idx = max(0, i * hop_length - pad_samples)
            break

    # Search from end
    for i in range(num_frames - 1, -1, -1):
        chunk = mono[i * hop_length : i * hop_length + frame_length]
        rms = np.sqrt(np.mean(chunk ** 2) + 1e-12)
        if rms >= threshold_linear:
            end_idx = min(len(audio), i * hop_length + frame_length + pad_samples)
            break

    if start_idx >= end_idx:
        return audio

    return audio[start_idx:end_idx]

def normalize_lufs(
    audio: np.ndarray,
    sr: int,
    target_lufs: float = -20.0,
    peak_limit: float = 0.95,
) -> np.ndarray:
    """
    Normalizes audio volume to target LUFS (-20.0 LUFS) using ITU-R BS.1770-4.
    Applies peak limiting to prevent digital clipping.
    """
    if len(audio) == 0:
        return audio

    # pyloudnorm expects shape (samples, channels) or (samples,)
    meter = pyln.Meter(sr)
    try:
        loudness = meter.integrated_loudness(audio)
        if not np.isinf(loudness) and not np.isnan(loudness) and loudness > -70.0:
            norm_audio = pyln.normalize.loudness(audio, loudness, target_lufs)
        else:
            # Fallback to RMS/Peak normalize
            peak = np.max(np.abs(audio))
            norm_audio = audio / peak * 0.75 if peak > 0 else audio
    except Exception as e:
        print(f"[AudioCleaner] Warning in LUFS calculation ({e}), fallback to peak normalization.")
        peak = np.max(np.abs(audio))
        norm_audio = audio / peak * 0.75 if peak > 0 else audio

    # Guard against clipping above peak_limit (-0.45 dBFS)
    current_peak = np.max(np.abs(norm_audio))
    if current_peak > peak_limit:
        norm_audio = norm_audio * (peak_limit / current_peak)

    return norm_audio.astype(np.float32)

def clean_audio(
    input_path: str,
    output_path: Optional[str] = None,
    target_lufs: float = -20.0,
    trim_silence_enabled: bool = True,
    max_duration_sec: Optional[float] = None,
) -> str:
    """
    Complete audio cleaning pipeline:
    1. Loads audio (any format via soundfile)
    2. VAD: Trims leading & trailing silences (preserving 120ms safety pad)
    3. Clamps duration to max_duration_sec (e.g. 10.0s for reference voices to prevent token overflow)
    4. Normalizes volume to -20 LUFS with peak limiter
    5. Exports clean WAV file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Audio file not found: {input_path}")

    # Read audio
    audio, sr = sf.read(str(input_path), dtype='float32')

    # Trim leading/trailing silence
    if trim_silence_enabled and len(audio) > 0:
        audio = trim_silence(audio, sr, threshold_db=-42.0, pad_ms=120)

    # Clamp maximum duration if specified (e.g. 10-12s for reference cloning audio)
    if max_duration_sec is not None and max_duration_sec > 0 and len(audio) > 0:
        max_samples = int(sr * max_duration_sec)
        if len(audio) > max_samples:
            audio = audio[:max_samples]

    # Normalize to -20 LUFS
    audio = normalize_lufs(audio, sr, target_lufs=target_lufs, peak_limit=0.95)

    # Determine output path
    if not output_path:
        suffix = ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            output_path = tmp.name

    # Save as 16-bit PCM WAV
    sf.write(str(output_path), audio, sr, subtype='PCM_16')
    return str(output_path)

