import os
import time
import uuid
import gc
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import scipy.io.wavfile

import torch
from models_manager import STABLE_AUDIO_DIR, AUDIOLDM_DIR, STABLE_AUDIO_3_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs" / "sfx"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

class SFXEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.is_loaded = False
        self.stable_3_pipe = None
        self.is_stable_3_loaded = False
        self.audioldm_pipe = None
        self.is_audioldm_loaded = False
        print(f"[SFXEngine] Initialized on device: {self.device}")

    def load_model(self):
        """Loads Stable Audio Open pipeline onto CUDA (RTX 5080)."""
        if self.is_loaded and self.pipe is not None:
            return

        print(f"[SFXEngine] Loading Stable Audio Open pipeline onto {self.device}...")

        from diffusers import StableAudioPipeline

        # Determine path: local folder if files exist, else HuggingFace repo
        local_files = list(STABLE_AUDIO_DIR.glob("**/*.safetensors")) + list(STABLE_AUDIO_DIR.glob("**/model_index.json"))
        model_source = str(STABLE_AUDIO_DIR) if len(local_files) > 0 else "stabilityai/stable-audio-open-1.0"

        dtype = torch.float16 if self.device == "cuda" else torch.float32

        try:
            self.pipe = StableAudioPipeline.from_pretrained(
                model_source,
                torch_dtype=dtype,
            )
            self.pipe = self.pipe.to(self.device)
            # Memory optimization for modern GPUs
            if hasattr(self.pipe, "enable_attention_slicing"):
                self.pipe.enable_attention_slicing()

            self.is_loaded = True
            print(f"[SFXEngine] Stable Audio Open successfully loaded onto {self.device}!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[SFXEngine] CUDA initialization warning ({e}). Falling back to CPU...")
                try:
                    self.device = "cpu"
                    self.pipe = StableAudioPipeline.from_pretrained(
                        model_source,
                        torch_dtype=torch.float32,
                    ).to("cpu")
                    self.is_loaded = True
                    print("[SFXEngine] Stable Audio Open loaded successfully on CPU!")
                    return
                except Exception as e_cpu:
                    raise RuntimeError(f"Could not load Stable Audio Open on CPU: {e_cpu}")
            self.is_loaded = False
            print(f"[SFXEngine] Error loading Stable Audio Open: {e}")
            raise RuntimeError(f"Error loading Stable Audio Open: {e}")

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "low quality, harsh, distorted, speech",
        duration: float = 10.0,
        steps: int = 50,
        cfg_scale: float = 7.0,
        seed: int = -1
    ) -> str:
        """
        Generates 44.1kHz stereo sound effect from prompt using Stable Audio Open.
        Returns the relative URL path of the generated WAV file.
        """
        if not self.is_loaded:
            self.load_model()

        # Clamp duration between 1.0 and 47.0 seconds
        duration = max(1.0, min(47.0, float(duration)))

        # Setup generator for deterministic or random seed
        generator = None
        if seed is not None and seed >= 0:
            generator = torch.Generator(device=self.device).manual_seed(int(seed))

        filename = f"sfx_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[SFXEngine] Generating sound effect: '{prompt}' ({duration}s, {steps} steps)...")

        try:
            output = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                audio_end_in_s=duration,
                num_inference_steps=steps,
                guidance_scale=cfg_scale,
                generator=generator
            )

            # Extract audio tensor (channels, samples)
            audio = output.audios[0]
            # Convert to numpy (channels, samples) -> (samples, channels)
            audio_np = audio.T.cpu().float().numpy()

            # Sampling rate from pipeline (typically 44100 Hz)
            sr = getattr(self.pipe.vae, "sampling_rate", 44100)

            # Normalize to avoid clipping
            max_val = np.max(np.abs(audio_np))
            if max_val > 0.99:
                audio_np = audio_np / max_val * 0.99

            sf.write(str(output_path), audio_np, sr)
            print(f"[SFXEngine] SFX saved successfully to {output_path}")

            return f"/outputs/sfx/{filename}"

        except Exception as e:
            print(f"[SFXEngine] Generation error: {e}")
            raise RuntimeError(f"Fout bij Stable Audio generatie: {e}")

    def unload(self):
        """Frees pipeline from VRAM."""
        print("[SFXEngine] Unloading Stable Audio Open from VRAM...")
        self.pipe = None
        self.is_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def load_audioldm(self):
        """Loads AudioLDM 2 pipeline onto CUDA (RTX 5080)."""
        if self.is_audioldm_loaded and self.audioldm_pipe is not None:
            return

        print(f"[SFXEngine] Loading AudioLDM 2 pipeline onto {self.device}...")
        from diffusers import AudioLDM2Pipeline

        local_files = list(AUDIOLDM_DIR.glob("**/*.safetensors")) + list(AUDIOLDM_DIR.glob("**/*.bin"))
        model_source = str(AUDIOLDM_DIR) if len(local_files) > 0 else "cvssp/audioldm2"

        # CRITICAL FIX: AudioLDM 2 requires float32. Float16 causes severe numerical underflow
        # in the VAE decoder and CLAP projections, producing loud buzzing static, hiss, and muffled distortion.
        # On RTX 5080, float32 runs blazingly fast (~3-4s) with pristine, punchy acoustic clarity.
        dtype = torch.float32
        try:
            self.audioldm_pipe = AudioLDM2Pipeline.from_pretrained(
                model_source,
                torch_dtype=dtype,
            )
            self.audioldm_pipe = self.audioldm_pipe.to(self.device)
            if hasattr(self.audioldm_pipe, "enable_attention_slicing"):
                self.audioldm_pipe.enable_attention_slicing()

            self.is_audioldm_loaded = True
            print(f"[SFXEngine] AudioLDM 2 successfully loaded onto {self.device} in high-fidelity float32 (zero static)!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[SFXEngine] CUDA AudioLDM 2 warning ({e}). Falling back to CPU...")
                try:
                    self.device = "cpu"
                    self.audioldm_pipe = AudioLDM2Pipeline.from_pretrained(
                        model_source,
                        torch_dtype=torch.float32,
                    ).to("cpu")
                    self.is_audioldm_loaded = True
                    print("[SFXEngine] AudioLDM 2 loaded on CPU!")
                    return
                except Exception as e_cpu:
                    raise RuntimeError(f"Could not load AudioLDM 2 on CPU: {e_cpu}")
            self.is_audioldm_loaded = False
            raise RuntimeError(f"Error loading AudioLDM 2: {e}")

    def generate_audioldm(
        self,
        prompt: str,
        negative_prompt: str = "low quality, static, buzzing, white noise, hiss, distortion, muffled, speech, human voice",
        duration: float = 10.0,
        steps: int = 45,
        guidance_scale: float = 4.5,
        seed: int = -1
    ) -> str:
        """
        Generates sound effect from prompt using AudioLDM 2 (16kHz).
        Particularly effective for complex multi-event prompts and Foley action adherence.
        """
        if not self.is_audioldm_loaded:
            self.load_audioldm()

        duration = max(1.0, min(30.0, float(duration)))
        generator = None
        if seed is not None and seed >= 0:
            generator = torch.Generator(device=self.device).manual_seed(int(seed))

        filename = f"sfx_audioldm2_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[SFXEngine] Generating AudioLDM 2 SFX: '{prompt}' ({duration}s, {steps} steps)...")
        try:
            output = self.audioldm_pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                audio_length_in_s=duration,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator
            )

            # AudioLDM 2 returns numpy array of shape (samples,) or (1, samples)
            audio = output.audios[0]
            audio_np = np.asarray(audio, dtype=np.float32)
            if audio_np.ndim > 1 and audio_np.shape[0] == 1:
                audio_np = audio_np[0]

            # Normalize to avoid clipping
            max_val = np.max(np.abs(audio_np))
            if max_val > 0.99:
                audio_np = audio_np / max_val * 0.99

            sr = 16000
            sf.write(str(output_path), audio_np, sr)
            print(f"[SFXEngine] AudioLDM 2 SFX saved to {output_path}")
            return f"/outputs/sfx/{filename}"
        except Exception as e:
            print(f"[SFXEngine] AudioLDM 2 generation error: {e}")
            raise RuntimeError(f"Fout bij AudioLDM 2 generatie: {e}")

    def unload_audioldm(self):
        """Frees AudioLDM 2 from VRAM."""
        print("[SFXEngine] Unloading AudioLDM 2 from VRAM...")
        self.audioldm_pipe = None
        self.is_audioldm_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def load_stable_audio_3(self):
        """Loads Stable Audio 3 Medium pipeline onto CUDA (RTX 5080)."""
        if self.is_stable_3_loaded and self.stable_3_pipe is not None:
            return

        print(f"[SFXEngine] Loading Stable Audio 3 Medium pipeline onto {self.device}...")
        from diffusers import StableAudioPipeline

        local_files = list(STABLE_AUDIO_3_DIR.glob("**/*.safetensors")) + list(STABLE_AUDIO_3_DIR.glob("**/model_index.json"))
        model_source = str(STABLE_AUDIO_3_DIR) if len(local_files) > 0 else "stabilityai/stable-audio-3-medium"
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        try:
            self.stable_3_pipe = StableAudioPipeline.from_pretrained(
                model_source,
                torch_dtype=dtype,
            )
            self.stable_3_pipe = self.stable_3_pipe.to(self.device)
            if hasattr(self.stable_3_pipe, "enable_attention_slicing"):
                self.stable_3_pipe.enable_attention_slicing()

            self.is_stable_3_loaded = True
            print(f"[SFXEngine] Stable Audio 3 Medium successfully loaded onto {self.device}!")
        except Exception as e:
            if self.device == "cuda":
                print(f"[SFXEngine] CUDA Stable Audio 3 warning ({e}). Falling back to CPU...")
                try:
                    self.device = "cpu"
                    self.stable_3_pipe = StableAudioPipeline.from_pretrained(
                        model_source,
                        torch_dtype=torch.float32,
                    ).to("cpu")
                    self.is_stable_3_loaded = True
                    print("[SFXEngine] Stable Audio 3 Medium loaded on CPU!")
                    return
                except Exception as e_cpu:
                    raise RuntimeError(f"Could not load Stable Audio 3 Medium on CPU: {e_cpu}")
            self.is_stable_3_loaded = False
            raise RuntimeError(f"Error loading Stable Audio 3 Medium: {e}")

    def generate_stable_audio_3(
        self,
        prompt: str,
        negative_prompt: str = "low quality, harsh, distorted, speech",
        duration: float = 10.0,
        steps: int = 50,
        cfg_scale: float = 7.0,
        seed: int = -1
    ) -> str:
        """
        Generates 44.1kHz stereo sound effect from prompt using Stable Audio 3 Medium.
        Returns the relative URL path of the generated WAV file.
        """
        if not self.is_stable_3_loaded:
            self.load_stable_audio_3()

        duration = max(1.0, min(47.0, float(duration)))
        generator = None
        if seed is not None and seed >= 0:
            generator = torch.Generator(device=self.device).manual_seed(int(seed))

        filename = f"sfx_sa3_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[SFXEngine] Generating Stable Audio 3 Medium SFX: '{prompt}' ({duration}s, {steps} steps)...")
        try:
            output = self.stable_3_pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                audio_end_in_s=duration,
                num_inference_steps=steps,
                guidance_scale=cfg_scale,
                generator=generator
            )

            audio = output.audios[0]
            audio_np = audio.T.cpu().float().numpy()
            sr = getattr(self.stable_3_pipe.vae, "sampling_rate", 44100)

            max_val = np.max(np.abs(audio_np))
            if max_val > 0.99:
                audio_np = audio_np / max_val * 0.99

            sf.write(str(output_path), audio_np, sr)
            print(f"[SFXEngine] Stable Audio 3 SFX saved to {output_path}")
            return f"/outputs/sfx/{filename}"
        except Exception as e:
            print(f"[SFXEngine] Stable Audio 3 generation error: {e}")
            raise RuntimeError(f"Fout bij Stable Audio 3 generatie: {e}")

    def unload_stable_audio_3(self):
        """Frees Stable Audio 3 Medium from VRAM."""
        print("[SFXEngine] Unloading Stable Audio 3 Medium from VRAM...")
        self.stable_3_pipe = None
        self.is_stable_3_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

sfx_engine = SFXEngine()

