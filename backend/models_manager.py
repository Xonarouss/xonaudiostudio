import os
import shutil
import gc
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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
LLAMA_DIR = MODELS_DIR / "llama"
OUTPUTS_DIR = BASE_DIR / "outputs"
VERSION_CACHE_FILE = MODELS_DIR / ".version_cache.json"

# Ensure directories exist
F5_DIR.mkdir(parents=True, exist_ok=True)
STABLE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
LLAMA_DIR.mkdir(parents=True, exist_ok=True)

def is_llama_installed() -> bool:
    """Checks if Llama weights exist in models/llama."""
    if not LLAMA_DIR.exists():
        return False
    files = list(LLAMA_DIR.glob("**/*.safetensors")) + list(LLAMA_DIR.glob("**/*.bin")) + list(LLAMA_DIR.glob("**/*.gguf"))
    return len(files) > 0

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
        "stable_audio": {
            "name": "Stable Audio Open 1.0",
            "repo": "stabilityai/stable-audio-open-1.0",
            "installed": stable_ready,
            "size_gb": f"{stable_size:.2f}",
            "path": str(STABLE_AUDIO_DIR),
            "vram_estimate": "4.5 GB"
        },
        "llama": {
            "name": "Llama 3 Local AI (Assistant & Prompt Enhancer)",
            "repo": "unsloth/Llama-3.2-1B-Instruct",
            "installed": llama_ready,
            "size_gb": f"{llama_size:.2f}",
            "path": str(LLAMA_DIR),
            "vram_estimate": "2.8 GB"
        }
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
        try:
            snapshot_download(
                repo_id="stabilityai/stable-audio-open-1.0",
                local_dir=str(STABLE_AUDIO_DIR),
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

    if model_key in ("llama", "all"):
        if LLAMA_DIR.exists():
            shutil.rmtree(LLAMA_DIR, ignore_errors=True)
            LLAMA_DIR.mkdir(parents=True, exist_ok=True)
            deleted_items.append("Llama 3 Local AI")

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
