import os
import time
import uuid
import gc
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import soundfile as sf

import torch
import torchaudio

from models_manager import F5_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs" / "tts"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

class TTSEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.vocoder = None
        self.is_loaded = False
        print(f"[TTSEngine] Initialized on device: {self.device}")

    def load_model(self):
        """Loads F5-TTS checkpoint into GPU memory."""
        if self.is_loaded and self.model is not None:
            return

        print(f"[TTSEngine] Loading F5-TTS onto {self.device}...")

        # Search for local checkpoint in F5_DIR
        ckpt_files = list(F5_DIR.glob("**/*.safetensors")) + list(F5_DIR.glob("**/*.pt"))
        vocab_files = list(F5_DIR.glob("**/vocab.txt"))

        ckpt_file = str(ckpt_files[0]) if ckpt_files else None
        vocab_file = str(vocab_files[0]) if vocab_files else None

        try:
            # Try importing official f5_tts
            from f5_tts.infer.utils_infer import load_model as f5_load_model, load_vocoder
            from f5_tts.model import CFM, DiT

            # Default model params
            model_cls = DiT
            model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

            self.model = f5_load_model(
                model_cls=model_cls,
                model_cfg=model_cfg,
                ckpt_path=ckpt_file or "F5TTS_v1_Base/model_1200000.safetensors",
                vocab_file=vocab_file,
                device=self.device
            )
            self.vocoder = load_vocoder(vocoder_name="vocos", is_local=False, local_path="")
            self.is_loaded = True
            print("[TTSEngine] F5-TTS successfully loaded!")
        except Exception as e:
            print(f"[TTSEngine] Note on loading f5-tts: {e}")
            # Try high-level F5TTS API if available
            try:
                from f5_tts.api import F5TTS
                self.model = F5TTS(model_type="F5-TTS", ckpt_file=ckpt_file, vocab_file=vocab_file, device=self.device)
                self.is_loaded = True
                print("[TTSEngine] F5-TTS high level API loaded!")
            except Exception as e2:
                print(f"[TTSEngine] Warning: Could not instantiate F5-TTS yet: {e2}")
                self.is_loaded = False
                raise RuntimeError(f"F5-TTS model initialisatie mislukt: {e2}")

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
        if not self.is_loaded:
            self.load_model()

        filename = f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[TTSEngine] Generating audio for text ({len(gen_text)} chars)...")

        # Create dummy reference if none provided
        temp_ref_created = False
        if not ref_audio_path or not os.path.exists(ref_audio_path):
            dummy_ref = OUTPUTS_DIR / "_default_ref.wav"
            if not dummy_ref.exists():
                # Generate a clean 3-second tone or silence as baseline
                sr = 24000
                t = np.linspace(0, 3, sr * 3, endpoint=False)
                tone = 0.1 * np.sin(2 * np.pi * 220 * t)
                sf.write(str(dummy_ref), tone, sr)
            ref_audio_path = str(dummy_ref)
            if not ref_text:
                ref_text = "Hallo en welkom."
            temp_ref_created = True

        try:
            # If using f5_tts.api.F5TTS
            if hasattr(self.model, 'infer'):
                wav, sr, _ = self.model.infer(
                    ref_file=ref_audio_path,
                    ref_text=ref_text,
                    gen_text=gen_text,
                    file_wave=str(output_path),
                    speed=speed,
                    nfe_step=nfe_steps,
                    remove_silence=remove_silence
                )
            else:
                # Direct infer_process
                from f5_tts.infer.utils_infer import infer_process
                wav, sr, _ = infer_process(
                    ref_audio=ref_audio_path,
                    ref_text=ref_text,
                    gen_text=gen_text,
                    model_obj=self.model,
                    vocoder=self.vocoder,
                    mel_spec_type="vocos",
                    speed=speed,
                    nfe_step=nfe_steps,
                    device=self.device
                )
                sf.write(str(output_path), wav, sr)

            print(f"[TTSEngine] Generated successfully: {output_path}")
            return f"/outputs/tts/{filename}"

        except Exception as e:
            print(f"[TTSEngine] Error during F5-TTS inference: {e}")
            raise RuntimeError(f"F5-TTS generatiefout: {e}")

    def unload(self):
        """Frees model from VRAM."""
        print("[TTSEngine] Unloading F5-TTS from VRAM...")
        self.model = None
        self.vocoder = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

tts_engine = TTSEngine()

