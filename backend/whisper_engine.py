import os
import gc
import torch
from pathlib import Path
from typing import Optional, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
WHISPER_DIR = BASE_DIR / "models" / "whisper-medium"

class WhisperEngine:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        print(f"[WhisperEngine] Configured for device: {self.device}")

    def load_model(self):
        if self.is_loaded and self.model is not None:
            return

        from faster_whisper import WhisperModel

        model_path = str(WHISPER_DIR) if WHISPER_DIR.exists() else "medium"
        compute_type = "float16" if self.device == "cuda" else "int8"

        print(f"[WhisperEngine] Loading Faster-Whisper ({model_path}) on {self.device} ({compute_type})...")
        try:
            self.model = WhisperModel(
                model_path,
                device=self.device,
                compute_type=compute_type,
            )
            self.is_loaded = True
            print(f"[WhisperEngine] Faster-Whisper successfully loaded on {self.device}!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[WhisperEngine] CUDA load error ({e}). Falling back to CPU...")
                self.device = "cpu"
                self.model = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                )
                self.is_loaded = True
                print("[WhisperEngine] Faster-Whisper loaded on CPU fallback!")
            else:
                self.is_loaded = False
                raise RuntimeError(f"Could not load Faster-Whisper: {e}")

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes the given audio file using Faster-Whisper.
        Returns a dict with 'text', 'language', 'probability', and 'duration'.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if not self.is_loaded or self.model is None:
            self.load_model()

        # Normalize language code (e.g. "nl" for Dutch, "en" for English)
        lang = language.strip().lower() if language and language.strip() else None
        if lang in ("auto", "none", ""):
            lang = None

        print(f"[WhisperEngine] Transcribing '{audio_path}' (language={lang or 'auto-detect'})...")

        segments, info = self.model.transcribe(
            audio_path,
            language=lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=250),
        )

        # Collect segment texts
        full_text = " ".join(seg.text.strip() for seg in segments).strip()

        print(f"[WhisperEngine] Detected language: '{info.language}' (prob: {info.language_probability:.2f}), Duration: {info.duration:.2f}s")
        print(f"[WhisperEngine] Transcript: \"{full_text}\"")

        return {
            "text": full_text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
        }

    def unload(self):
        """Unload Whisper model to free VRAM."""
        print("[WhisperEngine] Unloading Whisper model from memory...")
        self.model = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

whisper_engine = WhisperEngine()

