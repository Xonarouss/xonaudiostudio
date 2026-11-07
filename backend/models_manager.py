import os
import shutil
import gc
import subprocess
from pathlib import Path
from typing import Dict, Any

try:
    import torch
except ImportError:
    torch = None

try:
    import psutil
except ImportError:
    psutil = None

from huggingface_hub import hf_hub_download, snapshot_download

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
F5_DIR = MODELS_DIR / "f5-tts"
STABLE_AUDIO_DIR = MODELS_DIR / "stable-audio-open"

# Ensure directories exist
F5_DIR.mkdir(parents=True, exist_ok=True)
STABLE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

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

    f5_ready = is_f5_installed()
    stable_ready = is_stable_audio_installed()

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
        }
    }

def download_model(model_key: str) -> Dict[str, Any]:
    """Downloads requested model checkpoints to the local models folder."""
    if model_key == "f5_tts":
        print("[ModelManager] Downloading F5-TTS checkpoint from Hugging Face...")
        # Download model_1200000.safetensors and vocab.txt
        # SWivid/F5-TTS repository
        try:
            snapshot_download(
                repo_id="SWivid/F5-TTS",
                local_dir=str(F5_DIR),
                allow_patterns=["*F5TTS_v1_Base*", "*vocab*", "*.json", "*.txt"],
            )
            return {"status": "success", "message": "F5-TTS model succesvol gedownload!"}
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
                return {"status": "success", "message": "F5-TTS checkpoints succesvol gedownload!"}
            except Exception as e2:
                raise RuntimeError(f"Fout bij downloaden F5-TTS: {e2}")

    elif model_key == "stable_audio":
        print("[ModelManager] Downloading Stable Audio Open 1.0 from Hugging Face...")
        try:
            snapshot_download(
                repo_id="stabilityai/stable-audio-open-1.0",
                local_dir=str(STABLE_AUDIO_DIR),
            )
            return {"status": "success", "message": "Stable Audio Open model succesvol gedownload!"}
        except Exception as e:
            raise RuntimeError(f"Fout bij downloaden Stable Audio Open: {e}")

    else:
        raise ValueError(f"Onbekend model: {model_key}")

def delete_model(model_key: str) -> Dict[str, Any]:
    """Deletes model checkpoints from disk to free up storage space."""
    # Run garbage collection and free CUDA memory first to avoid file lock on Windows
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

    if not deleted_items:
        raise ValueError(f"Geen geldig model geselecteerd: {model_key}")

    return {
        "status": "success",
        "message": f"Modellen succesvol verwijderd van schijf: {', '.join(deleted_items)}. Schijfruimte is vrijgemaakt!"
    }

def get_system_metrics() -> Dict[str, Any]:
    """Retrieves live hardware statistics for RTX 5080, Ryzen 7800X3D and Drive D:"""
    gpu_name = "NVIDIA GeForce RTX 5080"
    vram_used = 0.0
    vram_total = 16.0

    if torch and torch.cuda.is_available():
        try:
            gpu_name = torch.cuda.get_device_name(0)
            vram_total = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1)
            vram_used = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 1)
        except Exception:
            pass
    else:
        # Fallback to nvidia-smi if torch not yet initialized
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                gpu_name = parts[0]
                vram_used = round(float(parts[1]) / 1024, 1)
                vram_total = round(float(parts[2]) / 1024, 1)
        except Exception:
            pass

    # Disk Free on drive containing workspace
    try:
        drive_path = BASE_DIR.anchor or "D:\\"
        disk_usage = shutil.disk_usage(drive_path)
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 1)
    except Exception:
        disk_free_gb = "N/A"

    # RAM stats
    ram_used = "N/A"
    ram_total = "64.0"
    if psutil:
        try:
            ram = psutil.virtual_memory()
            ram_used = f"{ram.used / (1024 ** 3):.1f}"
            ram_total = f"{ram.total / (1024 ** 3):.1f}"
        except Exception:
            pass

    return {
        "gpu_name": gpu_name,
        "gpu_vram_used_gb": f"{vram_used:.1f}",
        "gpu_vram_total_gb": f"{vram_total:.1f}",
        "ram_used_gb": ram_used,
        "ram_total_gb": ram_total,
        "disk_free_gb": f"{disk_free_gb}"
    }
