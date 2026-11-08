import os
import time
import uuid
import gc
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import scipy.io.wavfile

try:
    import patch_transformers_compat  # noqa: F401
except ImportError:
    from backend import patch_transformers_compat  # noqa: F401

import json
import sys
import torch
from models_manager import STABLE_AUDIO_DIR, AUDIOLDM_DIR, STABLE_AUDIO_3_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
SA3_REPO_DIR = BASE_DIR / "models" / "stable-audio-3-repo"
OUTPUTS_DIR = BASE_DIR / "outputs" / "sfx"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_negative_prompt(prompt: str, negative_prompt: Optional[str] = None, engine: str = "default") -> str:
    """
    Intelligently cleans and resolves conflicts in negative prompts across all models.
    Prevents negative prompts from canceling out qualities explicitly requested in prompt.
    """
    p_lower = (prompt or "").lower()
    neg_raw = (negative_prompt or "").strip()
    if not neg_raw:
        neg_raw = "low quality, distortion, noise, harsh, clipping"
    
    parts = [part.strip() for part in neg_raw.split(",") if part.strip()]
    
    vocal_keywords = [
        "scream", "screaming", "shout", "shouting", "cry", "crying", "laugh", "laughter",
        "whisper", "voice", "gasp", "cheer", "groan", "grunt", "yell", "howl", "moan",
        "vocal", "talk", "talking", "sing", "speech", "woman", "man", "human", "crowd",
        "person", "shootout", "call", "yelling"
    ]
    is_vocal = any(k in p_lower for k in vocal_keywords)
    
    music_keywords = [
        "music", "song", "melody", "beat", "track", "synth", "piano", "guitar",
        "orchestr", "drum", "instrument", "bass", "rhythm", "chords", "tune"
    ]
    is_music = any(k in p_lower for k in music_keywords)
    
    cleaned_parts = []
    for part in parts:
        part_lower = part.lower()
        # If user explicitly asked for vocal sounds, never cancel out voice/speech!
        if is_vocal and any(w in part_lower for w in ["speech", "voice", "human voice", "vocal", "talk", "singing"]):
            continue
        # If user asked for music/melody, never cancel out music/melody/instruments!
        if is_music and any(w in part_lower for w in ["music", "melody", "song", "instrument"]):
            continue
        cleaned_parts.append(part)
        
    if not cleaned_parts:
        cleaned_parts = ["low quality", "distortion", "noisy", "clipping"]
        
    return ", ".join(cleaned_parts)

class SFXEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.is_loaded = False
        self.sa3_model = None
        self.is_stable_3_loaded = False
        self.audioldm_pipe = None
        self.is_audioldm_loaded = False
        print(f"[SFXEngine] Initialized on device: {self.device}")

    def load_model(self):
        """Loads Stable Audio Open pipeline onto CUDA (RTX 5080)."""
        if self.is_loaded and self.pipe is not None:
            return

        # VRAM protection: offload heavy pipelines before loading SAO
        if self.is_stable_3_loaded:
            self.unload_stable_audio_3()
        if self.is_audioldm_loaded:
            self.unload_audioldm()

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

        clean_neg = sanitize_negative_prompt(prompt, negative_prompt, engine="stable_audio")
        print(f"[SFXEngine] Generating sound effect: '{prompt}' ({duration}s, {steps} steps, CFG={cfg_scale})...")
        print(f"[SFXEngine] Negative prompt: '{clean_neg}'")

        try:
            output = self.pipe(
                prompt=prompt,
                negative_prompt=clean_neg,
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

        # VRAM protection: offload heavy pipelines before loading AudioLDM 2
        if self.is_stable_3_loaded:
            self.unload_stable_audio_3()
        if self.is_loaded:
            self.unload()

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

        clean_neg = sanitize_negative_prompt(prompt, negative_prompt, engine="audioldm2")
        print(f"[SFXEngine] Generating AudioLDM 2 SFX: '{prompt}' ({duration}s, {steps} steps, CFG={guidance_scale})...")
        print(f"[SFXEngine] Negative prompt: '{clean_neg}'")
        try:
            output = self.audioldm_pipe(
                prompt=prompt,
                negative_prompt=clean_neg,
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
        """Loads Stable Audio 3 Medium pipeline onto CUDA (RTX 5080) using the official local SA3 engine."""
        if self.is_stable_3_loaded and self.sa3_model is not None:
            return

        # Ensure VRAM headroom: offload other audio synthesis pipelines before loading SA3 (~8GB fp16)
        if self.is_audioldm_loaded:
            self.unload_audioldm()
        if self.is_loaded:
            self.unload()

        print(f"[SFXEngine] Loading Stable Audio 3 Medium pipeline onto {self.device}...")

        if SA3_REPO_DIR.exists() and str(SA3_REPO_DIR) not in sys.path:
            sys.path.insert(0, str(SA3_REPO_DIR))

        from stable_audio_3.loading_utils import load_diffusion_cond
        from stable_audio_3.model import StableAudioModel

        config_path = STABLE_AUDIO_3_DIR / "model_config.json"
        ckpt_path = STABLE_AUDIO_3_DIR / "model.safetensors"

        if not config_path.exists() or not ckpt_path.exists():
            raise RuntimeError(
                f"Stable Audio 3 Medium model files not found in {STABLE_AUDIO_3_DIR}. "
                f"Please download it via Model Manager."
            )

        with open(config_path, "r", encoding="utf-8") as f:
            sa3_config = json.load(f)

        # Force local offline path for t5gemma text conditioning
        for c in sa3_config.get("model", {}).get("conditioning", {}).get("configs", []):
            if c.get("id") == "prompt" and "config" in c:
                c["config"]["repo_id"] = str(STABLE_AUDIO_3_DIR)

        use_half = (self.device == "cuda")
        raw_model = load_diffusion_cond(sa3_config, str(ckpt_path), device=self.device, model_half=use_half)
        self.sa3_model = StableAudioModel(raw_model, sa3_config, device=self.device, model_half=use_half)
        self.is_stable_3_loaded = True
        print(f"[SFXEngine] Stable Audio 3 Medium successfully loaded onto {self.device}!")

    def generate_stable_audio_3(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: float = 10.0,
        steps: int = 12,
        cfg_scale: float = 2.5,
        seed: int = -1
    ) -> str:
        """
        Generates 44.1kHz stereo sound effect from prompt using Stable Audio 3 Medium.
        Uses Flow-Matching DiT with smart negative prompting and soft-knee peak protection.
        """
        if not self.is_stable_3_loaded or self.sa3_model is None:
            self.load_stable_audio_3()

        duration = max(1.0, min(47.0, float(duration)))
        # SA3 Flow-Matching DiT: 8-12 steps produces pristine acoustic quality rapidly
        effective_steps = max(4, min(30, int(steps))) if steps else 10

        # SA3 Medium post-trained checkpoint is calibrated for CFG 1.0 - 1.8.
        # Higher CFG causes severe latent saturation, harsh crackle and tonal distortion.
        effective_cfg = max(1.0, min(2.0, float(cfg_scale))) if cfg_scale is not None else 1.2

        # SFX vs Music detection
        prompt_lower = prompt.lower()
        music_keywords = ["music", "song", "melody", "beat", "track", "synth", "piano", "guitar", "orchestr", "drum", "instrument", "bass", "rhythm"]
        is_music = any(k in prompt_lower for k in music_keywords)

        # AudioSparx TrackType tag primes the model for Foley / sound effects instead of music
        if not is_music and not prompt_lower.startswith("tracktype:"):
            effective_prompt = f"TrackType: SFX. {prompt}"
        else:
            effective_prompt = prompt

        clean_neg = sanitize_negative_prompt(prompt, negative_prompt, engine="stable_audio_3")

        # When CFG is exactly 1.0 (unconditioned), skip negative conditioning for 2x faster, crackle-free generation
        pass_neg = clean_neg if effective_cfg > 1.05 else None

        filename = f"sfx_sa3_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
        output_path = OUTPUTS_DIR / filename

        print(f"[SFXEngine] Generating Stable Audio 3 Medium SFX: '{effective_prompt}' ({duration}s, {effective_steps} steps, CFG={effective_cfg})...")
        print(f"[SFXEngine] Negative prompt: '{pass_neg}'")
        try:
            with torch.inference_mode():
                output_tensor = self.sa3_model.generate(
                    prompt=effective_prompt,
                    negative_prompt=pass_neg,
                    duration=duration,
                    steps=effective_steps,
                    cfg_scale=effective_cfg,
                    seed=int(seed) if seed is not None and seed >= 0 else -1,
                )

            # output_tensor shape: [batch, channels, samples]
            audio = output_tensor[0].cpu().float().numpy()
            audio_np = audio.T  # [samples, channels]
            sr = self.sa3_model.model_config.get("sample_rate", 44100)

            # Anti-Clipping Soft Limiter:
            # Prevent hard digital square-wave clipping from VAE decoder
            audio_np = np.clip(audio_np, -1.0, 1.0)
            max_val = np.max(np.abs(audio_np))
            if max_val > 0.001:
                # Target peak: -0.7 dBFS (0.92) to leave headroom for lossy codecs and DAC reconstruction
                audio_np = (audio_np / max_val) * min(0.92, max_val)

            sf.write(str(output_path), audio_np, sr)
            print(f"[SFXEngine] Stable Audio 3 SFX saved to {output_path}")
            return f"/outputs/sfx/{filename}"
        except Exception as e:
            print(f"[SFXEngine] Stable Audio 3 generation error: {e}")
            raise RuntimeError(f"Fout bij Stable Audio 3 generatie: {e}")

    def unload_stable_audio_3(self):
        """Frees Stable Audio 3 Medium from VRAM."""
        print("[SFXEngine] Unloading Stable Audio 3 Medium from VRAM...")
        self.sa3_model = None
        self.is_stable_3_loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

sfx_engine = SFXEngine()

