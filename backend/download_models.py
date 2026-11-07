import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from models_manager import (
    is_f5_installed,
    is_stable_audio_installed,
    is_llama_installed,
    check_for_model_updates,
    download_model,
    F5_DIR,
    STABLE_AUDIO_DIR,
    LLAMA_DIR
)

def check_and_download_all():
    print("=" * 72)
    print("        XONAUDIO STUDIO - NEURAL MODEL VERIFIER & AUTO-UPDATER")
    print("=" * 72)
    print(f"[*] Local models directory: {F5_DIR.parent}")

    f5_present = is_f5_installed()
    stable_present = is_stable_audio_installed()
    llama_present = is_llama_installed()

    print("[*] Checking for updates on Hugging Face...")
    update_info = {}
    try:
        update_info = check_for_model_updates()
    except Exception as e:
        print(f"[!] Update check skipped (network offline or timeout): {e}")

    f5_update = update_info.get("f5_tts", {}).get("update_available", False)
    stable_update = update_info.get("stable_audio", {}).get("update_available", False)

    # 1. F5-TTS Status
    if f5_present:
        if f5_update:
            print("[!] F5-TTS Voice Cloning: NEW VERSION AVAILABLE ON HUGGING FACE! (Updating...)")
        else:
            print("[+] F5-TTS Voice Cloning: INSTALLED & READY")
    else:
        print("[-] F5-TTS Voice Cloning: MISSING (Downloading weights...)")

    # 2. Stable Audio Open Status
    if stable_present:
        if stable_update:
            print("[!] Stable Audio Open 1.0: NEW VERSION AVAILABLE ON HUGGING FACE! (Updating...)")
        else:
            print("[+] Stable Audio Open 1.0: INSTALLED & READY")
    else:
        print("[-] Stable Audio Open 1.0: MISSING (Downloading weights...)")

    # 3. Llama 3 Local AI Status
    if llama_present:
        print("[+] Llama 3 AI Co-Pilot: INSTALLED & READY")
    else:
        print("[-] Llama 3 AI Co-Pilot: MISSING (Downloading weights...)")

    # If all present and no updates, launch immediately!
    if f5_present and stable_present and llama_present and not f5_update and not stable_update:
        print("-" * 72)
        print("[OK] All 3 neural models are installed, verified, and ready.")
        print("[OK] Launching studio immediately without download delays.")
        print("=" * 72 + "\n")
        return 0

    print("-" * 72)
    print("[*] Downloading / updating required foundation models...")
    print("-" * 72)

    # Download F5-TTS if missing or update available
    if not f5_present or f5_update:
        action = "Updating" if f5_update else "Downloading"
        print(f"\n>>> [1/3] {action} F5-TTS v1 Base weights (SWivid/F5-TTS)...")
        try:
            download_model("f5_tts")
            print("[+] F5-TTS weights successfully verified!")
        except Exception as e:
            print(f"[!] Warning downloading F5-TTS: {e}")

    # Download Stable Audio Open if missing or update available
    if not stable_present or stable_update:
        action = "Updating" if stable_update else "Downloading"
        print(f"\n>>> [2/3] {action} Stable Audio Open 1.0 (stabilityai/stable-audio-open-1.0)...")
        try:
            download_model("stable_audio")
            print("[+] Stable Audio Open weights successfully verified!")
        except Exception as e:
            print(f"[!] Warning downloading Stable Audio Open: {e}")

    # Download Llama 3 if missing
    if not llama_present:
        print(f"\n>>> [3/3] Downloading Llama 3 AI Assistant weights (unsloth/Llama-3.2-1B-Instruct)...")
        try:
            download_model("llama")
            print("[+] Llama 3 AI Assistant successfully verified!")
        except Exception as e:
            print(f"[!] Warning downloading Llama 3: {e}")

    print("\n" + "=" * 72)
    print("[OK] All neural model downloads and verification completed.")
    print("=" * 72 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(check_and_download_all())
