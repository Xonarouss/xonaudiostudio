"""
Fish Speech 1.5 Engine — Best-in-class quality TTS, fully local.
Model: fishaudio/fish-speech-1.5 (~700 MB weights)
Languages: English, Chinese, Japanese, Korean, French, German, Arabic, Spanish,
           Dutch, Portuguese, Italian, Russian (and more via zero-shot cloning)
Architecture: Dual Autoregressive (DAR) + VQ-GAN decoder — runs 100% on-device.
No network calls during inference. All processing on your GPU/CPU.
"""
import os
import gc
import sys
import time
import uuid
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
FISH_MODEL_DIR = BASE_DIR / "models" / "fish-speech-1.5"
FISH_REPO_DIR = BASE_DIR / "models" / "fish-speech-repo"
OUTPUTS_DIR = BASE_DIR / "outputs" / "tts"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Languages supported natively via training data (zero-shot cloning extends further)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
    "es": "Spanish",
    "nl": "Dutch",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
}


class FishEngine:
    """
    Runs Fish Speech 1.5 fully locally using their Python module directly
    (no subprocess server, no network calls during inference).
    Falls back to subprocess CLI if the Python API import fails.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = None
        self._decoder = None
        self._tokenizer = None
        self.is_loaded = False
        print(f"[FishEngine] Initialized on device: {self.device}")

    def is_installed(self) -> bool:
        """Check if Fish Speech model weights exist in models/fish-speech-1.5."""
        if not FISH_MODEL_DIR.exists():
            return False
        # Weights: model.pth, codec.pth, or safetensors files
        weights = (
            list(FISH_MODEL_DIR.glob("*.pth"))
            + list(FISH_MODEL_DIR.glob("*.safetensors"))
            + list(FISH_MODEL_DIR.glob("*.ckpt"))
        )
        return len(weights) > 0

    def _get_python_exe(self) -> str:
        """Return the venv Python executable path."""
        venv_python = BASE_DIR / "venv" / "Scripts" / "python.exe"
        return str(venv_python) if venv_python.exists() else sys.executable

    def load_model(self):
        """Load Fish Speech model into VRAM using their Python API."""
        if self.is_loaded and self._model is not None:
            return
        if not self.is_installed():
            raise RuntimeError(
                "Fish Speech 1.5 model is not installed. Please download it in Model Manager."
            )

        # Add fish-speech repo to sys.path so we can import it
        if FISH_REPO_DIR.exists() and str(FISH_REPO_DIR) not in sys.path:
            sys.path.insert(0, str(FISH_REPO_DIR))

        print(f"[FishEngine] Loading Fish Speech 1.5 on {self.device}...")

        try:
            # Try direct Python import (fastest, stays in-process)
            self._load_via_python_api()
        except Exception as e:
            print(f"[FishEngine] Python API load failed ({e}), will use CLI subprocess mode.")
            # CLI mode doesn't need model loaded here — inference handles it per-call
            self.is_loaded = True  # Mark as "ready" for CLI mode
            self._model = "cli"  # Sentinel

    def _load_via_python_api(self):
        """Load model directly via fish_speech Python module."""
        from fish_speech.models.text2semantic.inference import load_model as load_llm
        from fish_speech.models.vqgan.inference import load_model as load_vqgan

        precision = torch.bfloat16 if self.device == "cuda" else torch.float32

        # Load the LLM (text → semantic tokens)
        self._model, self._tokenizer = load_llm(
            checkpoint_path=str(FISH_MODEL_DIR),
            device=self.device,
            precision=precision,
            compile=False,
        )

        # Load the VQ-GAN decoder (semantic tokens → audio)
        decoder_path = FISH_MODEL_DIR / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
        if not decoder_path.exists():
            # Try any .pth that looks like a decoder/codec
            for f in FISH_MODEL_DIR.glob("*.pth"):
                if any(k in f.name.lower() for k in ["firefly", "decoder", "codec", "gan"]):
                    decoder_path = f
                    break

        self._decoder = load_vqgan(
            config_name="firefly_gan_vq",
            checkpoint_path=str(decoder_path),
            device=self.device,
        )

        self.is_loaded = True
        print("[FishEngine] Fish Speech 1.5 loaded successfully via Python API!")

    def _generate_via_python_api(
        self,
        gen_text: str,
        ref_audio_path: Optional[str],
        ref_text: str,
        output_path: Path,
        speed: float,
    ):
        """Generate audio using the in-process Python API."""
        import numpy as np
        import soundfile as sf
        from fish_speech.models.text2semantic.inference import generate as gen_semantic
        from fish_speech.models.vqgan.inference import decode_to_file

        precision = torch.bfloat16 if self.device == "cuda" else torch.float32

        # Encode reference audio into semantic tokens (for voice cloning)
        prompt_tokens = None
        prompt_text = None
        if ref_audio_path and os.path.exists(ref_audio_path):
            from fish_speech.models.vqgan.inference import encode_reference
            prompt_tokens, prompt_text_encoded = encode_reference(
                decoder=self._decoder,
                reference_audio=ref_audio_path,
                device=self.device,
            )
            if ref_text:
                prompt_text = ref_text

        # Generate semantic tokens
        codes = gen_semantic(
            model=self._model,
            tokenizer=self._tokenizer,
            device=self.device,
            text=gen_text,
            prompt_tokens=prompt_tokens,
            prompt_text=prompt_text,
            max_new_tokens=1024,
            top_p=0.7,
            repetition_penalty=1.5,
            temperature=0.7,
            compile=False,
            iterative_prompt=True,
        )

        # Decode to audio and save
        decode_to_file(
            decoder=self._decoder,
            codes=codes,
            output_path=str(output_path),
            device=self.device,
        )

    def _generate_via_cli(
        self,
        gen_text: str,
        ref_audio_path: Optional[str],
        ref_text: str,
        output_path: Path,
        speed: float,
    ):
        """
        Fallback: run Fish Speech inference via subprocess CLI.
        This is 100% local — no network calls. We call their inference script directly.
        """
        python_exe = self._get_python_exe()

        # Try different known script paths across versions
        infer_scripts = [
            FISH_REPO_DIR / "tools" / "infer.py",
            FISH_REPO_DIR / "tools" / "cli.py",
            FISH_REPO_DIR / "fish_speech" / "cli" / "inference.py",
        ]
        infer_script = next((s for s in infer_scripts if s.exists()), None)

        if infer_script is None:
            raise RuntimeError(
                "Fish Speech inference script not found. "
                "Please re-download Fish Speech in Model Manager to restore the repository files."
            )

        cmd = [
            python_exe,
            str(infer_script),
            "--text", gen_text,
            "--checkpoint-path", str(FISH_MODEL_DIR),
            "--output-path", str(output_path),
        ]

        if ref_audio_path and os.path.exists(ref_audio_path):
            cmd += ["--reference-audio", ref_audio_path]
            if ref_text:
                cmd += ["--reference-text", ref_text]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(FISH_REPO_DIR)

        print(f"[FishEngine] Running CLI inference: {' '.join(cmd[:4])}...")
        result = subprocess.run(
            cmd,
            cwd=str(FISH_REPO_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            stderr = result.stderr[-600:] if result.stderr else "no stderr"
            raise RuntimeError(f"Fish Speech CLI failed (exit {result.returncode}):\n{stderr}")

    def generate(
        self,
        gen_text: str,
        ref_audio_path: Optional[str] = None,
        ref_text: str = "",
        language: str = "en",
        speed: float = 1.0,
        emotion: str = "",
    ) -> str:
        """Generate speech using Fish Speech 1.5 — fully local."""
        if not self.is_loaded or self._model is None:
            self.load_model()

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            language = "en"

        # Prepend emotion stage direction to text
        effective_text = (
            f"{emotion.strip()} {gen_text}" if emotion and emotion.strip() else gen_text
        )

        filename = f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(
            f"[FishEngine] Generating {SUPPORTED_LANGUAGES.get(language, language)} "
            f"speech ({len(gen_text)} chars)..."
        )

        try:
            if self._model == "cli":
                # CLI subprocess mode
                self._generate_via_cli(effective_text, ref_audio_path, ref_text, output_path, speed)
            else:
                # In-process Python API mode
                self._generate_via_python_api(effective_text, ref_audio_path, ref_text, output_path, speed)

            if not output_path.exists():
                raise RuntimeError("Fish Speech generated no output file.")

            print(f"[FishEngine] Audio generated: {output_path}")
            return f"/outputs/tts/{filename}"

        except Exception as e:
            print(f"[FishEngine] Generation error: {e}")
            raise RuntimeError(f"Fish Speech 1.5 Error: {e}")

    def unload(self):
        """Free Fish Speech from VRAM."""
        print("[FishEngine] Unloading Fish Speech 1.5 from VRAM...")
        self._model = None
        self._decoder = None
        self._tokenizer = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


fish_engine = FishEngine()

