"""
XTTS-v2 Engine — Multilingual voice cloning supporting 17 languages including Dutch.
Model: coqui/XTTS-v2 from Hugging Face (~2.0 GB)
Supports: en, nl, de, fr, es, it, pt, pl, tr, ru, cs, ar, zh-cn, ja, hu, ko, hi
"""
import os
import gc
import time
import uuid
from pathlib import Path
from typing import Optional
import torch

try:
    import patch_torchaudio
except ImportError:
    from backend import patch_torchaudio

BASE_DIR = Path(__file__).resolve().parent.parent
XTTS_DIR = BASE_DIR / "models" / "xtts-v2"
OUTPUTS_DIR = BASE_DIR / "outputs" / "tts"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_LANGUAGES = {
    "en": "English", "nl": "Dutch", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "pl": "Polish",
    "tr": "Turkish", "ru": "Russian", "cs": "Czech", "ar": "Arabic",
    "zh-cn": "Chinese", "ja": "Japanese", "hu": "Hungarian", "ko": "Korean", "hi": "Hindi"
}

class XTTSEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = None
        self.is_loaded = False
        print(f"[XTTSEngine] Initialized on device: {self.device}")

    def is_installed(self) -> bool:
        if not XTTS_DIR.exists():
            return False
        # Check for model config and weights
        has_config = (XTTS_DIR / "config.json").exists() or len(list(XTTS_DIR.glob("**/*.json"))) > 0
        has_weights = len(list(XTTS_DIR.glob("**/*.pth"))) > 0 or len(list(XTTS_DIR.glob("**/*.safetensors"))) > 0
        return has_config and has_weights

    def load_model(self):
        if self.is_loaded and self.tts is not None:
            return
        if not self.is_installed():
            raise RuntimeError("XTTS-v2 model is not installed. Please download it in Model Manager.")

        print(f"[XTTSEngine] Loading XTTS-v2 on {self.device}...")
        _orig_torch_load = torch.load
        def _safe_load(*args, **kwargs):
            if "weights_only" not in kwargs:
                kwargs["weights_only"] = False
            return _orig_torch_load(*args, **kwargs)

        try:
            torch.load = _safe_load
            from TTS.api import TTS as CoquiTTS
            # Load from local directory
            config_path = None
            for f in XTTS_DIR.glob("**/*.json"):
                if "config" in f.name.lower():
                    config_path = str(f)
                    break

            self.tts = CoquiTTS(
                model_path=str(XTTS_DIR),
                config_path=config_path or str(XTTS_DIR / "config.json"),
                progress_bar=False
            ).to(self.device)
            self.is_loaded = True
            print("[XTTSEngine] XTTS-v2 loaded successfully!")
        except Exception as e:
            self.is_loaded = False
            print(f"[XTTSEngine] Error loading XTTS-v2: {e}")
            raise RuntimeError(f"Could not load XTTS-v2: {e}")
        finally:
            torch.load = _orig_torch_load

    def generate(
        self,
        gen_text: str,
        ref_audio_path: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        emotion: str = ""
    ) -> str:
        if not self.is_loaded or self.tts is None:
            self.load_model()

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            language = "en"

        # Use clean text directly (never prepend stage directions to spoken text)
        effective_text = gen_text

        filename = f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[XTTSEngine] Generating {SUPPORTED_LANGUAGES.get(language, language)} speech ({len(gen_text)} chars)...")

        # Determine speaker reference audio (XTTS-v2 clones from a reference wav)
        effective_ref = None
        if ref_audio_path and os.path.exists(ref_audio_path):
            effective_ref = str(ref_audio_path)
        elif (BASE_DIR / "voices" / "aria.wav").exists():
            effective_ref = str(BASE_DIR / "voices" / "aria.wav")
        else:
            samples = list(XTTS_DIR.glob("**/*.wav"))
            if samples:
                effective_ref = str(samples[0])

        if not effective_ref or not os.path.exists(effective_ref):
            raise RuntimeError("XTTS-v2 requires a reference voice (.wav). No voice sample found.")

        try:
            self.tts.tts_to_file(
                text=effective_text,
                speaker_wav=effective_ref,
                language=language,
                file_path=str(output_path),
                speed=speed
            )
            print(f"[XTTSEngine] Audio generated: {output_path}")
            return f"/outputs/tts/{filename}"
        except Exception as e:
            print(f"[XTTSEngine] Generation error: {e}")
            raise RuntimeError(f"XTTS-v2 Generation Error: {e}")

    def unload(self):
        print("[XTTSEngine] Unloading XTTS-v2 from VRAM...")
        self.tts = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

xtts_engine = XTTSEngine()
