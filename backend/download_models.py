import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from models_manager import (
    is_f5_installed,
    is_stable_audio_installed,
    is_llama_installed,
    is_xtts_installed,
    is_fish_installed,
    is_audioldm_installed,
    is_whisper_installed,
    check_for_model_updates,
    download_model,
    MODELS_DIR,
    F5_DIR,
    STABLE_AUDIO_DIR,
    LLAMA_DIR,
    XTTS_DIR,
    FISH_MODEL_DIR,
    AUDIOLDM_DIR,
    WHISPER_DIR
)

FIRST_LAUNCH_FLAG = MODELS_DIR / ".first_launch_done"

MODELS_CATALOG = {
    "1": {
        "key": "f5_tts",
        "name": "F5-TTS Voice Cloning",
        "size": "~2.5 GB",
        "is_installed": is_f5_installed,
        "arch": "Flow-Matching Diffusion (SWivid/F5-TTS)",
        "what_it_does": "Non-autoregressive speech synthesis and zero-shot voice cloning from 5s audio.",
        "use_for": "Fast narration, audiobooks, podcast voices, instant zero-shot voice cloning.",
        "recommendation": "[HIGHLY RECOMMENDED - Core Voice Lab Engine]"
    },
    "2": {
        "key": "fish_speech",
        "name": "Fish Speech 1.5 Ultra",
        "size": "~1.4 GB",
        "is_installed": is_fish_installed,
        "arch": "Dual Autoregressive Transformer + Firefly VQ-GAN",
        "what_it_does": "Autoregressive expressive voice synthesis with native emotion tag decoding.",
        "use_for": "Emotional acting, drama, laughter & expressive cues ([laugh], [sigh], [gasp], [whisper]), 13+ languages.",
        "recommendation": "[HIGHLY RECOMMENDED for emotion, laughter & dialogue]"
    },
    "3": {
        "key": "xtts",
        "name": "Coqui XTTS-v2 Multilingual",
        "size": "~2.0 GB",
        "is_installed": is_xtts_installed,
        "arch": "Dual-path Diffusion + GPT speaker latent encoder",
        "what_it_does": "High-fidelity multilingual voice cloning across 17 languages.",
        "use_for": "Dutch (Nederlands), German, French, Spanish, Italian, and European voiceovers.",
        "recommendation": "[RECOMMENDED if you need Dutch or 17 European languages]"
    },
    "4": {
        "key": "audioldm2",
        "name": "AudioLDM 2 Studio (Multi-Event SFX)",
        "size": "~1.8 GB",
        "is_installed": is_audioldm_installed,
        "arch": "Dual CLAP + T5 Conditioning Latent Diffusion (cvssp/audioldm2)",
        "what_it_does": "Multi-event action adherence sound effect synthesis up to 30s.",
        "use_for": "Composite Foley prompts with multiple actions (e.g. 'reversing car screeching tires', 'footsteps then door slam').",
        "recommendation": "[HIGHLY RECOMMENDED - Solves missed sounds in composite prompts]"
    },
    "5": {
        "key": "stable_audio",
        "name": "Stable Audio Open 1.0",
        "size": "~4.8 GB",
        "is_installed": is_stable_audio_installed,
        "arch": "Continuous Latent Audio Diffusion (stabilityai/stable-audio-open-1.0)",
        "what_it_does": "High-fidelity 44.1kHz stereo audio diffusion up to 47 seconds.",
        "use_for": "Long ambient beds (thunderstorm, rain, room tone), continuous sci-fi drones, instrumental loops.",
        "recommendation": "[RECOMMENDED for 44.1kHz hi-fi ambient beds & continuous textures]"
    },
    "6": {
        "key": "llama",
        "name": "Llama 3.2 1B Instruct Local AI",
        "size": "~2.3 GB",
        "is_installed": is_llama_installed,
        "arch": "Meta Llama 3 running 100% locally on CUDA",
        "what_it_does": "Intelligent prompt expansion, acoustic styling, and voice scriptwriting assistant.",
        "use_for": "Magic Wand prompt optimization to turn simple ideas into Hollywood acoustic prompts.",
        "recommendation": "[RECOMMENDED for AI prompt enhancement & creative suggestions]"
    },
    "7": {
        "key": "whisper",
        "name": "Faster-Whisper Medium (Voice ASR & Cleaner)",
        "size": "~1.5 GB",
        "is_installed": is_whisper_installed,
        "arch": "CTranslate2 Faster-Whisper on CUDA (Systran/faster-whisper-medium)",
        "what_it_does": "Instant 100% reference voice auto-transcription and audio cleaning pipeline (-20 LUFS).",
        "use_for": "Eliminating voice cloning word hallucinations & repeats by generating exact reference text.",
        "recommendation": "[HIGHLY RECOMMENDED for flawless voice cloning without hallucination]"
    }
}

def print_banner():
    print("==========================================================================")
    print("            XONAUDIO STUDIO - AI MODEL SCANNER & SETUP WIZARD")
    print("                     Built by Xonarous Inc (xonarous.nl)")
    print("==========================================================================")

def scan_all_models():
    """Scans and prints the current status of all 6 AI models."""
    print("\n[*] Current Neural Model Installation Status:")
    print("-" * 72)
    for idx, info in MODELS_CATALOG.items():
        installed = info["is_installed"]()
        status_tag = "[INSTALLED & READY]" if installed else "[NOT INSTALLED]"
        print(f"  {idx}. {info['name']} ({info['size']}) -> {status_tag}")
    print("-" * 72)

def interactive_first_launch_wizard():
    print_banner()
    print("\n[!] Welcome to your first launch of XonAudio Studio!")
    print("    To run 100% locally on your GPU, choose which AI models you want to set up.")
    print("    Below is a breakdown of what each model does, its use cases, and recommendations:\n")

    for idx, info in MODELS_CATALOG.items():
        installed = info["is_installed"]()
        status_str = " (Already Installed)" if installed else ""
        print(f"[{idx}] {info['name']} ({info['size']}){status_str}")
        print(f"    Architecture:   {info['arch']}")
        print(f"    What it does:   {info['what_it_does']}")
        print(f"    Best use case:  {info['use_for']}")
        print(f"    Recommendation: {info['recommendation']}")
        print()

    print("=" * 72)
    print("  QUICK PRESETS:")
    print("  [A] All Recommended Models (~16 GB)  - Complete AI Audio Workstation")
    print("  [V] Voice Studio Only (~6.8 GB)      - F5-TTS + Fish Speech + XTTS-v2")
    print("  [S] Sound Effects Only (~6.6 GB)     - AudioLDM 2 + Stable Audio Open")
    print("  [M] Minimal Setup (~4.1 GB)          - F5-TTS + AudioLDM 2 (Fastest download)")
    print("  [C] Custom selection                 - Pick specific model numbers (e.g. 1,2,4)")
    print("  [N] Skip for now                     - Launch immediately (download anytime in UI)")
    print("=" * 72)

    choice = input("\n[?] Enter your choice [A / V / S / M / C / N] (default: A): ").strip().upper()
    if not choice:
        choice = "A"

    keys_to_download = []
    if choice == "A":
        keys_to_download = ["f5_tts", "fish_speech", "xtts", "audioldm2", "stable_audio", "llama", "whisper"]
    elif choice == "V":
        keys_to_download = ["f5_tts", "fish_speech", "xtts", "whisper"]
    elif choice == "S":
        keys_to_download = ["audioldm2", "stable_audio"]
    elif choice == "M":
        keys_to_download = ["f5_tts", "audioldm2"]
    elif choice == "N":
        print("\n[*] Skipping initial downloads. You can download models anytime in Model Manager!")
        FIRST_LAUNCH_FLAG.write_text("done\n", encoding="utf-8")
        return 0
    elif choice == "C":
        print("\nEnter numbers separated by commas (e.g. 1, 2, 4):")
        num_input = input("[?] Numbers: ").strip()
        for part in num_input.split(","):
            part = part.strip()
            if part in MODELS_CATALOG:
                keys_to_download.append(MODELS_CATALOG[part]["key"])

    if not keys_to_download:
        print("[!] No valid models selected. Proceeding to launch studio...")
        FIRST_LAUNCH_FLAG.write_text("done\n", encoding="utf-8")
        return 0

    print("\n" + "=" * 72)
    print(f"[*] Starting download of selected models: {', '.join(keys_to_download)}")
    print("=" * 72)

    for key in keys_to_download:
        # Find model catalog entry
        entry = next((v for v in MODELS_CATALOG.values() if v["key"] == key), None)
        if entry and entry["is_installed"]():
            print(f"\n[+] {entry['name']} is already installed on disk. Skipping.")
            continue

        name = entry['name'] if entry else key
        print(f"\n>>> Downloading {name}...")
        try:
            download_model(key)
            print(f"[+] Successfully verified and installed: {name}!")
        except Exception as e:
            print(f"[!] Warning while installing {name}: {e}")
            print(f"    (You can retry downloading {name} later inside the Model Manager UI)")

    FIRST_LAUNCH_FLAG.write_text("done\n", encoding="utf-8")
    print("\n[+] First-time model setup completed!")
    print("=" * 72 + "\n")
    return 0

def check_and_download_all():
    """Main entrypoint run by Start_AudioStudio.bat."""
    # Check if first launch wizard has run
    force_wizard = "--wizard" in sys.argv or "-w" in sys.argv
    if not FIRST_LAUNCH_FLAG.exists() or force_wizard:
        return interactive_first_launch_wizard()

    # Normal launch: scan and report installed models quickly
    print_banner()
    scan_all_models()

    # If essential minimum model (F5-TTS) is missing, offer quick download
    if not is_f5_installed():
        print("\n[!] Core F5-TTS model is not installed.")
        print("[*] Downloading F5-TTS checkpoint for immediate voice generation...")
        try:
            download_model("f5_tts")
            print("[+] F5-TTS is now installed and ready!")
        except Exception as e:
            print(f"[!] Warning downloading F5-TTS: {e}")

    print("\n[+] Studio launch checks complete. Starting services...\n")
    return 0

if __name__ == "__main__":
    sys.exit(check_and_download_all())
