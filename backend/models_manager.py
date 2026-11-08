import os
import shutil
import gc
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import torch
except ImportError:
    torch = None

try:
    import psutil
except ImportError:
    psutil = None

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
F5_DIR = MODELS_DIR / "f5-tts"
STABLE_AUDIO_DIR = MODELS_DIR / "stable-audio-open"
STABLE_AUDIO_3_DIR = MODELS_DIR / "stable-audio-3-medium"
LLAMA_DIR = MODELS_DIR / "llama"
XTTS_DIR = MODELS_DIR / "xtts-v2"
FISH_MODEL_DIR = MODELS_DIR / "fish-speech-1.5"
FISH_REPO_DIR = MODELS_DIR / "fish-speech-repo"
AUDIOLDM_DIR = MODELS_DIR / "audioldm2"
STABLE_AUDIO_SMALL_DIR = MODELS_DIR / "stable-audio-open-small"
WHISPER_DIR = MODELS_DIR / "whisper-medium"
BS_ROFORMER_DIR = MODELS_DIR / "bs_roformer"
RVC_DIR = MODELS_DIR / "rvc"
OUTPUTS_DIR = BASE_DIR / "outputs"
VERSION_CACHE_FILE = MODELS_DIR / ".version_cache.json"

# Ensure directories exist
F5_DIR.mkdir(parents=True, exist_ok=True)
STABLE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
STABLE_AUDIO_3_DIR.mkdir(parents=True, exist_ok=True)
LLAMA_DIR.mkdir(parents=True, exist_ok=True)
XTTS_DIR.mkdir(parents=True, exist_ok=True)
FISH_MODEL_DIR.mkdir(parents=True, exist_ok=True)
FISH_REPO_DIR.mkdir(parents=True, exist_ok=True)
AUDIOLDM_DIR.mkdir(parents=True, exist_ok=True)
STABLE_AUDIO_SMALL_DIR.mkdir(parents=True, exist_ok=True)
WHISPER_DIR.mkdir(parents=True, exist_ok=True)
BS_ROFORMER_DIR.mkdir(parents=True, exist_ok=True)
RVC_DIR.mkdir(parents=True, exist_ok=True)

def is_llama_installed() -> bool:
    """Checks if Llama weights exist in models/llama."""
    if not LLAMA_DIR.exists():
        return False
    files = list(LLAMA_DIR.glob("**/*.safetensors")) + list(LLAMA_DIR.glob("**/*.bin")) + list(LLAMA_DIR.glob("**/*.gguf"))
    return len(files) > 0

def is_xtts_installed() -> bool:
    """Checks if XTTS-v2 weights exist in models/xtts-v2."""
    if not XTTS_DIR.exists():
        return False
    has_weights = len(list(XTTS_DIR.glob("**/*.pth"))) > 0 or len(list(XTTS_DIR.glob("**/*.safetensors"))) > 0
    return has_weights

def is_fish_installed() -> bool:
    """Checks if Fish Speech 1.5 weights exist in models/fish-speech-1.5."""
    if not FISH_MODEL_DIR.exists():
        return False
    weights = (list(FISH_MODEL_DIR.glob("*.pth")) + list(FISH_MODEL_DIR.glob("*.safetensors"))
               + list(FISH_MODEL_DIR.glob("*.ckpt")))
    return len(weights) > 0

def is_audioldm_installed() -> bool:
    """Checks if AudioLDM 2 weights exist in models/audioldm2."""
    if not AUDIOLDM_DIR.exists():
        return False
    files = list(AUDIOLDM_DIR.glob("**/*.safetensors")) + list(AUDIOLDM_DIR.glob("**/*.bin"))
    return len(files) > 0

def is_whisper_installed() -> bool:
    """Checks if Faster-Whisper weights exist in models/whisper-medium."""
    if not WHISPER_DIR.exists():
        return False
    files = list(WHISPER_DIR.glob("*.bin")) + list(WHISPER_DIR.glob("*.safetensors"))
    return len(files) > 0

def is_stable_audio_3_installed() -> bool:
    """Checks if Stable Audio 3 Medium weights exist in models/stable-audio-3-medium."""
    if not STABLE_AUDIO_3_DIR.exists():
        return False
    files = list(STABLE_AUDIO_3_DIR.glob("**/*.safetensors")) + list(STABLE_AUDIO_3_DIR.glob("**/*.ckpt"))
    return len(files) > 0

def is_stable_audio_small_installed() -> bool:
    """Checks if Stable Audio Open Small weights exist in models/stable-audio-open-small."""
    if not STABLE_AUDIO_SMALL_DIR.exists():
        return False
    # stable-audio-tools saves model.ckpt / model.safetensors + model_config.json
    files = (list(STABLE_AUDIO_SMALL_DIR.glob("**/*.ckpt"))
             + list(STABLE_AUDIO_SMALL_DIR.glob("**/*.safetensors"))
             + list(STABLE_AUDIO_SMALL_DIR.glob("**/model_config.json")))
    return len(files) > 0

def is_bs_roformer_installed() -> bool:
    """Checks if BS-RoFormer vocal separator weights exist in models/bs_roformer."""
    if not BS_ROFORMER_DIR.exists():
        return False
    ckpts = list(BS_ROFORMER_DIR.glob("*.ckpt")) + list(BS_ROFORMER_DIR.glob("*.pth"))
    return len(ckpts) > 0

def is_rmvpe_installed() -> bool:
    """Checks if RMVPE neural pitch extractor weights exist in models/rvc."""
    if not RVC_DIR.exists():
        return False
    return (RVC_DIR / "rmvpe.pt").exists()

def is_rvc_models_installed() -> bool:
    """Checks if user RVC voice models (.pth files) exist in models/rvc."""
    if not RVC_DIR.exists():
        return False
    system_weights = {"rmvpe.pt", "hubert_base.pt", "hubert.pt"}
    user_pths = [p for p in RVC_DIR.glob("**/*.pth") if p.name.lower() not in system_weights]
    return len(user_pths) > 0

def load_version_cache() -> Dict[str, Any]:
    if VERSION_CACHE_FILE.exists():
        try:
            with open(VERSION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_version_cache(cache: Dict[str, Any]):
    try:
        with open(VERSION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[ModelManager] Warning saving version cache: {e}")

def get_remote_model_sha(repo_id: str) -> Optional[str]:
    """Retrieves the latest commit SHA of a Hugging Face model repository."""
    try:
        api = HfApi()
        info = api.model_info(repo_id=repo_id, timeout=6)
        return info.sha
    except Exception as e:
        return None

def check_for_model_updates() -> Dict[str, Dict[str, Any]]:
    """
    Checks if new weights/versions exist on Hugging Face for F5-TTS and Stable Audio Open.
    Returns status indicating whether an update is available.
    """
    cache = load_version_cache()
    repos = {
        "f5_tts": "SWivid/F5-TTS",
        "stable_audio": "stabilityai/stable-audio-open-1.0"
    }

    results = {}
    for key, repo in repos.items():
        is_installed = is_f5_installed() if key == "f5_tts" else is_stable_audio_installed()
        cached_info = cache.get(key, {})
        cached_sha = cached_info.get("sha")

        remote_sha = get_remote_model_sha(repo)

        update_available = False
        if is_installed and remote_sha and cached_sha and remote_sha != cached_sha:
            update_available = True

        results[key] = {
            "repo": repo,
            "installed": is_installed,
            "cached_sha": cached_sha,
            "remote_sha": remote_sha,
            "update_available": update_available
        }

    return results

def get_dir_size_gb(path: Path) -> float:
    """Calculates total size of a directory in GB."""
    if not path.exists():
        return 0.0
    total_bytes = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(fp)
            except OSError:
                pass
    return round(total_bytes / (1024 ** 3), 2)

def is_f5_installed() -> bool:
    """Checks if F5-TTS weights and vocab exist in models/f5-tts or HF cache."""
    if not F5_DIR.exists():
        return False
    # Check for safetensors file in folder or subfolders
    safetensors = list(F5_DIR.glob("**/*.safetensors")) + list(F5_DIR.glob("**/*.pt"))
    return len(safetensors) > 0

def is_stable_audio_installed() -> bool:
    """Checks if Stable Audio Open weights exist in models/stable-audio-open."""
    if not STABLE_AUDIO_DIR.exists():
        return False
    # Check for model index or safetensors files
    files = list(STABLE_AUDIO_DIR.glob("**/*.safetensors")) + list(STABLE_AUDIO_DIR.glob("**/model_index.json"))
    return len(files) > 0

def get_all_models_status() -> Dict[str, Any]:
    """Returns installation status and disk size of all managed AI models."""
    f5_size = get_dir_size_gb(F5_DIR)
    stable_size = get_dir_size_gb(STABLE_AUDIO_DIR)
    llama_size = get_dir_size_gb(LLAMA_DIR)
    xtts_size = get_dir_size_gb(XTTS_DIR)
    fish_size = get_dir_size_gb(FISH_MODEL_DIR)
    audioldm_size = get_dir_size_gb(AUDIOLDM_DIR)
    stable_small_size = get_dir_size_gb(STABLE_AUDIO_SMALL_DIR)
    stable_3_size = get_dir_size_gb(STABLE_AUDIO_3_DIR)
    whisper_size = get_dir_size_gb(WHISPER_DIR)
    bs_roformer_size = get_dir_size_gb(BS_ROFORMER_DIR)
    rvc_size = get_dir_size_gb(RVC_DIR)

    f5_ready = is_f5_installed()
    stable_ready = is_stable_audio_installed()
    llama_ready = is_llama_installed()

    return {
        "f5_tts": {
            "name": "F5-TTS Voice Cloning",
            "repo": "SWivid/F5-TTS",
            "installed": f5_ready,
            "size_gb": f"{f5_size:.2f}",
            "path": str(F5_DIR),
            "vram_estimate": "2.2 GB"
        },
        "xtts": {
            "name": "XTTS-v2 Multilingual Voice",
            "repo": "coqui/XTTS-v2",
            "installed": is_xtts_installed(),
            "size_gb": f"{xtts_size:.2f}",
            "path": str(XTTS_DIR),
            "vram_estimate": "~3.5 GB"
        },
        "fish_speech": {
            "name": "Fish Speech 1.5 Ultra",
            "repo": "fishaudio/fish-speech-1.5",
            "installed": is_fish_installed(),
            "size_gb": f"{fish_size:.2f}",
            "path": str(FISH_MODEL_DIR),
            "vram_estimate": "~2.0 GB"
        },
        "stable_audio": {
            "name": "Stable Audio Open 1.0",
            "repo": "stabilityai/stable-audio-open-1.0",
            "installed": stable_ready,
            "size_gb": f"{stable_size:.2f}",
            "path": str(STABLE_AUDIO_DIR),
            "vram_estimate": "4.5 GB"
        },
        "stable_audio_3": {
            "name": "Stable Audio 3 Medium (Flagship 44.1kHz)",
            "repo": "stabilityai/stable-audio-3-medium",
            "installed": is_stable_audio_3_installed(),
            "size_gb": f"{stable_3_size:.2f}",
            "path": str(STABLE_AUDIO_3_DIR),
            "vram_estimate": "4.8 GB",
            "description": "Stability AI flagship 2B Diffusion Transformer (DiT) with T5Gemma for studio sound design and foley."
        },
        "audioldm2": {
            "name": "AudioLDM 2 Studio (Multi-Event SFX)",
            "repo": "cvssp/audioldm2",
            "installed": is_audioldm_installed(),
            "size_gb": f"{audioldm_size:.2f}",
            "path": str(AUDIOLDM_DIR),
            "vram_estimate": "~2.5 GB",
            "description": "Dual CLAP + T5 conditioning designed for composite soundscapes & Foley actions (e.g. reversing car screeching tires)."
        },
        "stable_audio_small": {
            "name": "Stable Audio Open Small (Fast 44.1kHz)",
            "repo": "stabilityai/stable-audio-open-small",
            "installed": is_stable_audio_small_installed(),
            "size_gb": f"{stable_small_size:.2f}",
            "path": str(STABLE_AUDIO_SMALL_DIR),
            "vram_estimate": "~1.5 GB",
            "description": "Lightweight DiT model for rapid 44.1kHz stereo SFX & loops up to 11s. Runs on consumer GPUs with minimal VRAM."
        },
        "whisper": {
            "name": "Faster-Whisper Medium (Voice ASR & Cleaner)",
            "repo": "Systran/faster-whisper-medium",
            "installed": is_whisper_installed(),
            "size_gb": f"{whisper_size:.2f}",
            "path": str(WHISPER_DIR),
            "vram_estimate": "~1.5 GB",
            "description": "High-accuracy speech transcription & reference voice cleaner on CUDA float16."
        },
        "llama": {
            "name": "Llama 3 Local AI (Assistant & Prompt Enhancer)",
            "repo": "unsloth/Llama-3.2-1B-Instruct",
            "installed": llama_ready,
            "size_gb": f"{llama_size:.2f}",
            "path": str(LLAMA_DIR),
            "vram_estimate": "2.8 GB"
        },
        "bs_roformer": {
            "name": "BS-RoFormer Vocal Separator (~700 MB)",
            "repo": "TRvlvr/model_repo (ViperX SDR 12.97)",
            "installed": is_bs_roformer_installed(),
            "size_gb": f"{bs_roformer_size:.2f}",
            "path": str(BS_ROFORMER_DIR),
            "vram_estimate": "~1.5 GB",
            "description": "State-of-the-art Band-Split RoFormer for pristine vocal & instrumental isolation (used in Song Cover Lab)."
        },
        "rmvpe": {
            "name": "RMVPE Pitch Extractor (~150 MB)",
            "repo": "lj1995/VoiceConversionWebUI",
            "installed": is_rmvpe_installed(),
            "size_gb": f"{rvc_size:.2f}",
            "path": str(RVC_DIR / 'rmvpe.pt'),
            "vram_estimate": "~0.5 GB",
            "description": "Robust Model for Vocal Pitch Estimation (E2E polyphonic music pitch extraction for RVC v2)."
        },
        "rvc_voices": {
            "name": "RVC Voice Models (/models/rvc)",
            "repo": "User Imported (.pth / .index)",
            "installed": is_rvc_models_installed(),
            "size_gb": f"{rvc_size:.2f}",
            "path": str(RVC_DIR),
            "vram_estimate": "~1.0 GB",
            "description": "Custom RVC v2 voice conversion checkpoints (.pth) and feature indexes (.index) in /models/rvc."
        },
    }

def download_model(model_key: str) -> Dict[str, Any]:
    """Downloads requested model checkpoints to the local models folder."""
    if model_key == "f5_tts":
        print("[ModelManager] Downloading/Updating F5-TTS checkpoint from Hugging Face...")
        # Download model_1200000.safetensors and vocab.txt
        # SWivid/F5-TTS repository
        try:
            snapshot_download(
                repo_id="SWivid/F5-TTS",
                local_dir=str(F5_DIR),
                allow_patterns=["*F5TTS_v1_Base*", "*vocab*", "*.json", "*.txt"],
            )
            # Update cache with current remote SHA
            sha = get_remote_model_sha("SWivid/F5-TTS")
            cache = load_version_cache()
            cache["f5_tts"] = {"sha": sha, "updated_at": datetime.now().isoformat()}
            save_version_cache(cache)
            return {"status": "success", "message": "F5-TTS model succesvol gedownload en bijgewerkt!"}
        except Exception as e:
            # Fallback to direct file download
            try:
                hf_hub_download(
                    repo_id="SWivid/F5-TTS",
                    filename="F5TTS_v1_Base/model_1200000.safetensors",
                    local_dir=str(F5_DIR),
                )
                hf_hub_download(
                    repo_id="SWivid/F5-TTS",
                    filename="F5TTS_v1_Base/vocab.txt",
                    local_dir=str(F5_DIR),
                )
                sha = get_remote_model_sha("SWivid/F5-TTS")
                cache = load_version_cache()
                cache["f5_tts"] = {"sha": sha, "updated_at": datetime.now().isoformat()}
                save_version_cache(cache)
                return {"status": "success", "message": "F5-TTS checkpoints succesvol gedownload!"}
            except Exception as e2:
                raise RuntimeError(f"Fout bij downloaden F5-TTS: {e2}")

    elif model_key == "stable_audio":
        print("[ModelManager] Downloading/Updating Stable Audio Open 1.0 from Hugging Face...")
        hf_token = os.environ.get("HF_TOKEN", "").strip()
        if not hf_token:
            # Try loading from .env file
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("HF_TOKEN="):
                        hf_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not hf_token:
            raise RuntimeError(
                "Stable Audio Open 1.0 is a gated model on Hugging Face. "
                "You must accept the license at https://huggingface.co/stabilityai/stable-audio-open-1.0 "
                "and set your HF_TOKEN in the .env file (HF_TOKEN=hf_your_token_here)."
            )
        try:
            snapshot_download(
                repo_id="stabilityai/stable-audio-open-1.0",
                local_dir=str(STABLE_AUDIO_DIR),
                token=hf_token,
            )
            sha = get_remote_model_sha("stabilityai/stable-audio-open-1.0")
            cache = load_version_cache()
            cache["stable_audio"] = {"sha": sha, "updated_at": datetime.now().isoformat()}
            save_version_cache(cache)
            return {"status": "success", "message": "Stable Audio Open model downloaded successfully!"}
        except Exception as e:
            raise RuntimeError(f"Error downloading Stable Audio Open: {e}")

    elif model_key == "llama":
        print("[ModelManager] Downloading Llama 3 Instruct model from Hugging Face...")
        try:
            snapshot_download(
                repo_id="unsloth/Llama-3.2-1B-Instruct",
                local_dir=str(LLAMA_DIR),
            )
            sha = get_remote_model_sha("unsloth/Llama-3.2-1B-Instruct")
            cache = load_version_cache()
            cache["llama"] = {"sha": sha, "updated_at": datetime.now().isoformat()}
            save_version_cache(cache)
            return {"status": "success", "message": "Llama 3 Local AI model downloaded successfully!"}
        except Exception as e:
            raise RuntimeError(f"Error downloading Llama model: {e}")

    elif model_key == "xtts":
        print("[ModelManager] Downloading XTTS-v2 from Hugging Face (~2 GB)...")
        try:
            snapshot_download(
                repo_id="coqui/XTTS-v2",
                local_dir=str(XTTS_DIR),
            )
            return {"status": "success", "message": "XTTS-v2 multilingual model downloaded! Supports 17 languages including Dutch."}
        except Exception as e:
            raise RuntimeError(f"Error downloading XTTS-v2: {e}")

    elif model_key == "fish_speech":
        print("[ModelManager] Downloading Fish Speech 1.5 from Hugging Face (~700 MB)...")
        try:
            # Download model weights
            snapshot_download(
                repo_id="fishaudio/fish-speech-1.5",
                local_dir=str(FISH_MODEL_DIR),
            )
            # Clone the fish-speech repo for inference scripts
            if not (FISH_REPO_DIR / "fish_speech").exists():
                print("[ModelManager] Cloning fish-speech repository for inference scripts...")
                try:
                    result = subprocess.run(
                        ["git", "clone", "--depth=1",
                         "https://github.com/fishaudio/fish-speech.git",
                         str(FISH_REPO_DIR)],
                        capture_output=True, text=True, timeout=180
                    )
                    if result.returncode != 0:
                        print(f"[ModelManager] Git clone warning: {result.stderr[:200]}")
                except Exception as repo_err:
                    print(f"[ModelManager] Could not clone fish-speech repo: {repo_err}")
                    print("[ModelManager] Model weights downloaded. Install fish-speech manually if needed.")
            return {"status": "success", "message": "Fish Speech 1.5 downloaded! Ultra-high quality TTS ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading Fish Speech 1.5: {e}")

    elif model_key == "audioldm2":
        print("[ModelManager] Downloading AudioLDM 2 from Hugging Face (~1.8 GB)...")
        try:
            snapshot_download(
                repo_id="cvssp/audioldm2",
                local_dir=str(AUDIOLDM_DIR),
            )
            return {"status": "success", "message": "AudioLDM 2 downloaded! Multi-event Foley and complex sound design ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading AudioLDM 2: {e}")

    elif model_key == "stable_audio_3":
        print("[ModelManager] Downloading Stable Audio 3 Medium from Hugging Face (~4.8 GB)...")
        hf_token = os.environ.get("HF_TOKEN", "").strip()
        if not hf_token:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("HF_TOKEN="):
                        hf_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not hf_token:
            raise RuntimeError(
                "Stable Audio 3 Medium is a gated model on Hugging Face. "
                "You must accept the license at https://huggingface.co/stabilityai/stable-audio-3-medium "
                "and set your HF_TOKEN in the .env file (HF_TOKEN=hf_your_token_here)."
            )
        try:
            snapshot_download(
                repo_id="stabilityai/stable-audio-3-medium",
                local_dir=str(STABLE_AUDIO_3_DIR),
                token=hf_token,
            )
            return {"status": "success", "message": "Stable Audio 3 Medium downloaded successfully!"}
        except Exception as e:
            raise RuntimeError(f"Error downloading Stable Audio 3 Medium: {e}")

    elif model_key == "stable_audio_small":
        print("[ModelManager] Downloading Stable Audio Open Small from Hugging Face (~1.5 GB)...")
        hf_token = os.environ.get("HF_TOKEN", "").strip()
        if not hf_token:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("HF_TOKEN="):
                        hf_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not hf_token:
            raise RuntimeError(
                "Stable Audio Open Small is a gated model on Hugging Face. "
                "You must accept the license at https://huggingface.co/stabilityai/stable-audio-open-small "
                "and set your HF_TOKEN in the .env file (HF_TOKEN=hf_your_token_here)."
            )
        try:
            snapshot_download(
                repo_id="stabilityai/stable-audio-open-small",
                local_dir=str(STABLE_AUDIO_SMALL_DIR),
                token=hf_token,
            )
            return {"status": "success", "message": "Stable Audio Open Small downloaded! Fast 44.1kHz stereo SFX generation ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading Stable Audio Open Small: {e}")

    elif model_key == "whisper":
        print("[ModelManager] Downloading Faster-Whisper Medium from Hugging Face (~1.5 GB)...")
        try:
            snapshot_download(
                repo_id="Systran/faster-whisper-medium",
                local_dir=str(WHISPER_DIR),
            )
            return {"status": "success", "message": "Faster-Whisper Medium downloaded! Reference audio transcription & cleaner ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading Faster-Whisper: {e}")

    elif model_key == "bs_roformer":
        print("[ModelManager] Downloading BS-RoFormer Vocal Separator (~640 MB)...")
        try:
            from audio_separator.separator import Separator
            sep = Separator(model_file_dir=str(BS_ROFORMER_DIR))
            sep.load_model(model_filename="model_bs_roformer_ep_317_sdr_12.9755.ckpt")
            del sep
            return {"status": "success", "message": "BS-RoFormer Vocal Separator downloaded! Studio vocal isolation ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading BS-RoFormer: {e}")

    elif model_key == "rmvpe":
        print("[ModelManager] Downloading RMVPE Pitch Extractor & HuBERT weights (~330 MB)...")
        try:
            p1 = hf_hub_download(repo_id="lj1995/VoiceConversionWebUI", filename="rmvpe.pt", local_dir=str(RVC_DIR))
            p2 = hf_hub_download(repo_id="lj1995/VoiceConversionWebUI", filename="hubert_base.pt", local_dir=str(RVC_DIR))
            return {"status": "success", "message": "RMVPE and HuBERT neural models downloaded! RVC voice conversion ready."}
        except Exception as e:
            raise RuntimeError(f"Error downloading RMVPE / HuBERT: {e}")

    else:
        raise ValueError(f"Unknown model: {model_key}")

def delete_model(model_key: str) -> Dict[str, Any]:
    """Deletes model checkpoints from disk to free up storage space."""
    gc.collect()
    if torch and torch.cuda.is_available():
        torch.cuda.empty_cache()

    deleted_items = []

    if model_key in ("f5_tts", "all"):
        if F5_DIR.exists():
            shutil.rmtree(F5_DIR, ignore_errors=True)
            F5_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("F5-TTS")

    if model_key in ("stable_audio", "all"):
        if STABLE_AUDIO_DIR.exists():
            shutil.rmtree(STABLE_AUDIO_DIR, ignore_errors=True)
            STABLE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Stable Audio Open")

    if model_key in ("stable_audio_3", "all"):
        if STABLE_AUDIO_3_DIR.exists():
            shutil.rmtree(STABLE_AUDIO_3_DIR, ignore_errors=True)
            STABLE_AUDIO_3_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Stable Audio 3 Medium")

    if model_key in ("audioldm2", "all"):
        if AUDIOLDM_DIR.exists():
            shutil.rmtree(AUDIOLDM_DIR, ignore_errors=True)
            AUDIOLDM_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("AudioLDM 2")

    if model_key in ("stable_audio_small", "all"):
        if STABLE_AUDIO_SMALL_DIR.exists():
            shutil.rmtree(STABLE_AUDIO_SMALL_DIR, ignore_errors=True)
            STABLE_AUDIO_SMALL_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Stable Audio Open Small")

    if model_key in ("whisper", "all"):
        if WHISPER_DIR.exists():
            shutil.rmtree(WHISPER_DIR, ignore_errors=True)
            WHISPER_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Faster-Whisper")

    if model_key in ("llama", "all"):
        if LLAMA_DIR.exists():
            shutil.rmtree(LLAMA_DIR, ignore_errors=True)
            LLAMA_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Llama 3 Local AI")

    if model_key in ("xtts", "all"):
        if XTTS_DIR.exists():
            shutil.rmtree(XTTS_DIR, ignore_errors=True)
            XTTS_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("XTTS-v2")

    if model_key in ("fish_speech", "all"):
        if FISH_MODEL_DIR.exists():
            shutil.rmtree(FISH_MODEL_DIR, ignore_errors=True)
            FISH_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Fish Speech 1.5")

    if model_key in ("bs_roformer", "all"):
        if BS_ROFORMER_DIR.exists():
            shutil.rmtree(BS_ROFORMER_DIR, ignore_errors=True)
            BS_ROFORMER_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("BS-RoFormer")

    if model_key in ("rmvpe", "all"):
        rmvpe_file = RVC_DIR / "rmvpe.pt"
        if rmvpe_file.exists():
            rmvpe_file.unlink(missing_ok=True)
            deleted_items.append("RMVPE")
        hubert_file = RVC_DIR / "hubert_base.pt"
        if hubert_file.exists():
            hubert_file.unlink(missing_ok=True)
            deleted_items.append("HuBERT")

    if model_key in ("rvc_voices", "all"):
        # Delete user voice models in models/rvc, preserving rmvpe.pt and hubert_base.pt
        system_weights = {"rmvpe.pt", "hubert_base.pt", "hubert.pt"}
        del_count = 0
        for pth in RVC_DIR.glob("**/*.pth"):
            if pth.name.lower() not in system_weights:
                pth.unlink(missing_ok=True)
                del_count += 1
        for idx in RVC_DIR.glob("**/*.index"):
            idx.unlink(missing_ok=True)
        if del_count > 0:
            deleted_items.append(f"RVC Voice Models ({del_count} models)")

    if not deleted_items:
        raise ValueError(f"No valid model selected: {model_key}")

    return {
        "status": "success",
        "message": f"Successfully deleted from disk: {', '.join(deleted_items)}. Storage space reclaimed!"
    }

def get_all_generations() -> List[Dict[str, Any]]:
    """Scans and lists all generated audio files across TTS and SFX directories."""
    generations = []
    
    # Scan TTS outputs
    tts_dir = OUTPUTS_DIR / "tts"
    if tts_dir.exists():
        for file in tts_dir.glob("*.wav"):
            if file.name.startswith("_default"):
                continue
            try:
                stat = file.stat()
                generations.append({
                    "id": file.stem,
                    "filename": file.name,
                    "type": "tts",
                    "title": f"Voice Clip ({file.stem[-6:]})",
                    "url": f"/outputs/tts/{file.name}",
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M:%S"),
                    "timestamp": stat.st_mtime
                })
            except Exception:
                pass

    # Scan SFX outputs
    sfx_dir = OUTPUTS_DIR / "sfx"
    if sfx_dir.exists():
        for file in sfx_dir.glob("*.wav"):
            try:
                stat = file.stat()
                generations.append({
                    "id": file.stem,
                    "filename": file.name,
                    "type": "sfx",
                    "title": f"Sound Effect ({file.stem[-6:]})",
                    "url": f"/outputs/sfx/{file.name}",
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M:%S"),
                    "timestamp": stat.st_mtime
                })
            except Exception:
                pass

    # Scan Song Cover outputs
    song_covers_dir = OUTPUTS_DIR / "song_covers" / "mixes"
    if song_covers_dir.exists():
        # Scan WAV files first to represent primary studio masters
        for file in song_covers_dir.glob("*.wav"):
            try:
                stat = file.stat()
                if file.name.startswith("cover_mix_"):
                    title = f"AI Song Cover — Full Mix ({file.stem[-8:]})"
                elif file.name.startswith("cover_vocals_"):
                    title = f"Song Cover — Vocals Only ({file.stem[-8:]})"
                elif file.name.startswith("cover_inst_"):
                    title = f"Song Cover — Instrumental ({file.stem[-8:]})"
                else:
                    title = f"Song Cover ({file.stem[-8:]})"

                mp3_candidate = file.with_suffix(".mp3")
                mp3_url = f"/outputs/song_covers/mixes/{mp3_candidate.name}" if mp3_candidate.exists() else None

                generations.append({
                    "id": file.stem,
                    "filename": file.name,
                    "type": "song_cover",
                    "title": title,
                    "url": f"/outputs/song_covers/mixes/{file.name}",
                    "mp3_url": mp3_url,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M:%S"),
                    "timestamp": stat.st_mtime
                })
            except Exception:
                pass

        # Also include standalone MP3s if no corresponding WAV exists
        for file in song_covers_dir.glob("*.mp3"):
            wav_candidate = file.with_suffix(".wav")
            if not wav_candidate.exists():
                try:
                    stat = file.stat()
                    if file.name.startswith("cover_mix_"):
                        title = f"AI Song Cover — Full Mix ({file.stem[-8:]})"
                    elif file.name.startswith("cover_vocals_"):
                        title = f"Song Cover — Vocals Only ({file.stem[-8:]})"
                    elif file.name.startswith("cover_inst_"):
                        title = f"Song Cover — Instrumental ({file.stem[-8:]})"
                    else:
                        title = f"Song Cover ({file.stem[-8:]})"

                    generations.append({
                        "id": file.stem,
                        "filename": file.name,
                        "type": "song_cover",
                        "title": title,
                        "url": f"/outputs/song_covers/mixes/{file.name}",
                        "mp3_url": f"/outputs/song_covers/mixes/{file.name}",
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M:%S"),
                        "timestamp": stat.st_mtime
                    })
                except Exception:
                    pass

    # Sort newest first
    generations.sort(key=lambda x: x["timestamp"], reverse=True)
    return generations

def get_system_metrics() -> Dict[str, Any]:
    """Retrieves live dynamic hardware statistics matching Genux monitor widget."""
    gpu_name = "NVIDIA GPU"
    clean_name = "GPU"
    gpu_util = 0
    gpu_temp = 0
    vram_used = 0.0
    vram_total = 16.0
    power_draw = 0
    power_limit = 0

    # Query nvidia-smi dynamically
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw,power.limit", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True, timeout=3
        )
        line = res.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 7:
            gpu_name = parts[0]
            clean_name = gpu_name.replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")
            gpu_util = int(float(parts[1]))
            gpu_temp = int(float(parts[2]))
            vram_used = round(float(parts[3]) / 1024, 1)
            vram_total = round(float(parts[4]) / 1024, 1)
            power_draw = int(float(parts[5]))
            power_limit = int(float(parts[6]))
    except Exception:
        clean_name = gpu_name

    # CPU Utilization
    cpu_util = 0
    if psutil:
        try:
            cpu_util = int(psutil.cpu_percent(interval=None))
        except Exception:
            pass

    # RAM
    ram_used = "0.0"
    ram_total = "0.0"
    ram_percent = 0
    if psutil:
        try:
            mem = psutil.virtual_memory()
            ram_used = f"{mem.used / (1024 ** 3):.1f}"
            ram_total = f"{mem.total / (1024 ** 3):.1f}"
            ram_percent = int(mem.percent)
        except Exception:
            pass

    # Engine memory
    engine_mem = "0.1"
    if psutil:
        try:
            proc = psutil.Process()
            engine_mem = f"{proc.memory_info().rss / (1024 ** 3):.1f}"
        except Exception:
            pass

    # Disk Free on drive containing workspace
    disk_free_gb = "N/A"
    try:
        drive_path = BASE_DIR.anchor or "D:\\"
        disk_usage = shutil.disk_usage(drive_path)
        disk_free_gb = f"{disk_usage.free / (1024 ** 3):.1f}"
    except Exception:
        pass

    vram_pct = int((vram_used / max(vram_total, 1.0)) * 100)
    power_pct = int((power_draw / max(power_limit, 1)) * 100) if power_limit > 0 else 0

    return {
        "gpu_name": clean_name,
        "gpu_full_name": gpu_name,
        "gpu_util_percent": gpu_util,
        "gpu_temp_c": gpu_temp,
        "gpu_vram_used_gb": f"{vram_used:.1f}",
        "gpu_vram_total_gb": f"{vram_total:.1f}",
        "gpu_vram_percent": vram_pct,
        "power_draw_w": power_draw,
        "power_limit_w": power_limit,
        "power_percent": power_pct,
        "cpu_util_percent": cpu_util,
        "ram_used_gb": ram_used,
        "ram_total_gb": ram_total,
        "ram_percent": ram_percent,
        "engine_mem_gb": engine_mem,
        "disk_free_gb": disk_free_gb,
        "engine_status": "Engine Online"
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "download":
        m_name = sys.argv[2]
        print(f"[ModelManager CLI] Starting download for: {m_name}")
        res = download_model(m_name)
        print(f"[ModelManager CLI] Download result: {res}")
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        status = get_all_models_status()
        for k, v in status.items():
            state = "INSTALLED" if v["installed"] else "MISSING"
            print(f"  * {v['name']} ({k}): {state} [{v['size_gb']} GB]")

