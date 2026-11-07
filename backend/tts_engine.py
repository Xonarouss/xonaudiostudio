import os
import time
import uuid
import gc
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import torch

from models_manager import F5_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs" / "tts"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

class TTSEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.f5 = None
        self.is_loaded = False
        print(f"[TTSEngine] Initialized on device: {self.device}")

    def load_model(self):
        """Loads F5-TTS model onto CUDA/CPU."""
        if self.is_loaded and self.f5 is not None:
            return

        print(f"[TTSEngine] Loading F5-TTS onto {self.device}...")

        # Search for local checkpoints in F5_DIR
        ckpt_files = list(F5_DIR.glob("**/*.safetensors")) + list(F5_DIR.glob("**/*.pt"))
        vocab_files = list(F5_DIR.glob("**/vocab.txt"))

        ckpt_file = str(ckpt_files[0]) if ckpt_files else ""
        vocab_file = str(vocab_files[0]) if vocab_files else ""

        try:
            from f5_tts.api import F5TTS
            # Instantiate using official F5TTS api
            self.f5 = F5TTS(
                model="F5TTS_v1_Base",
                ckpt_file=ckpt_file,
                vocab_file=vocab_file,
                device=self.device
            )
            self.is_loaded = True
            print(f"[TTSEngine] F5-TTS successfully loaded on {self.device} into memory!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[TTSEngine] CUDA initialization error ({e}). Retrying with CPU fallback...")
                try:
                    self.device = "cpu"
                    from f5_tts.api import F5TTS
                    self.f5 = F5TTS(
                        model="F5TTS_v1_Base",
                        ckpt_file=ckpt_file,
                        vocab_file=vocab_file,
                        device="cpu"
                    )
                    self.is_loaded = True
                    print("[TTSEngine] F5-TTS successfully loaded on CPU!")
                    return
                except Exception as e_cpu:
                    raise RuntimeError(f"Could not load F5-TTS on CPU: {e_cpu}")
            self.is_loaded = False
            print(f"[TTSEngine] Error instantiating F5-TTS: {e}")
            raise RuntimeError(f"Could not load F5-TTS model: {e}")

    def generate(
        self,
        gen_text: str,
        ref_audio_path: Optional[str] = None,
        ref_text: str = "",
        speed: float = 1.0,
        nfe_steps: int = 32,
        remove_silence: bool = True
    ) -> str:
        """
        Synthesizes speech from text using F5-TTS voice cloning.
        Returns the relative URL path of the generated WAV file.
        """
        if not self.is_loaded or self.f5 is None:
            self.load_model()

        filename = f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[TTSEngine] Generating voice audio ({len(gen_text)} chars)...")

        # Provide clean default reference if none given
        if not ref_audio_path or not os.path.exists(ref_audio_path):
            default_ref = BASE_DIR / "backend" / "default_sample.wav"
            if not default_ref.exists():
                # Generate a clean 3-second gentle reference tone to bootstrap zero-shot
                sr = 24000
                t = np.linspace(0, 3, sr * 3, endpoint=False)
                tone = 0.05 * np.sin(2 * np.pi * 220 * t)
                sf.write(str(default_ref), tone, sr)
            ref_audio_path = str(default_ref)
            if not ref_text:
                ref_text = "Welcome to XonAudio Studio."

        try:
            wav, sr, _ = self.f5.infer(
                ref_file=ref_audio_path,
                ref_text=ref_text or "Hello there.",
                gen_text=gen_text,
                file_wave=str(output_path),
                speed=float(speed),
                nfe_step=int(nfe_steps),
                remove_silence=bool(remove_silence)
            )

            # Ensure file was written
            if not output_path.exists() and wav is not None:
                sf.write(str(output_path), wav, sr)

            print(f"[TTSEngine] Audio generated successfully: {output_path}")
            return f"/outputs/tts/{filename}"

        except Exception as e:
            print(f"[TTSEngine] Error during inference: {e}")
            raise RuntimeError(f"F5-TTS Voice Generation Error: {e}")

    def unload(self):
        """Frees model from VRAM."""
        print("[TTSEngine] Unloading F5-TTS from VRAM...")
        self.f5 = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

tts_engine = TTSEngine()
