import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from models_manager import (
    is_f5_installed,
    is_stable_audio_installed,
    check_for_model_updates,
    download_model,
    F5_DIR,
    STABLE_AUDIO_DIR
)

def check_and_download_all():
    print("=" * 68)
    print("        XONAUDIO STUDIO - MODEL VERIFICATIE & AUTO-UPDATE")
    print("=" * 68)
    print(f"[*] Lokale modelmap: {F5_DIR.parent}")

    f5_present = is_f5_installed()
    stable_present = is_stable_audio_installed()

    print("[*] Controleren op updates via Hugging Face...")
    update_info = {}
    try:
        update_info = check_for_model_updates()
    except Exception as e:
        print(f"[!] Updatecheck overgeslagen (geen internet of timeout): {e}")

    f5_update = update_info.get("f5_tts", {}).get("update_available", False)
    stable_update = update_info.get("stable_audio", {}).get("update_available", False)

    # Status reporting
    if f5_present:
        if f5_update:
            print("[!] F5-TTS: NIEUWE VERSIE BESCHIKBAAR OP HUGGING FACE! (Auto-updating...)")
        else:
            print("[+] F5-TTS Checkpoint: AANWEZIG & UP-TO-DATE")
    else:
        print("[-] F5-TTS Checkpoint: ONTBREEKT (Eerste download vereist)")

    if stable_present:
        if stable_update:
            print("[!] Stable Audio Open: NIEUWE VERSIE BESCHIKBAAR! (Auto-updating...)")
        else:
            print("[+] Stable Audio Open Checkpoint: AANWEZIG & UP-TO-DATE")
    else:
        print("[-] Stable Audio Open Checkpoint: ONTBREEKT (Eerste download vereist)")

    # If both installed and no updates, launch immediately
    if f5_present and stable_present and not f5_update and not stable_update:
        print("-" * 68)
        print("[OK] Alle modellen zijn up-to-date en lokaal aanwezig!")
        print("[OK] Studio start direct op zonder wachttijd.")
        print("=" * 68 + "\n")
        return 0

    print("-" * 68)
    print("[*] Bezig met binnenhalen of bijwerken van gewichten...")
    print("-" * 68)

    # Download or update F5-TTS
    if not f5_present or f5_update:
        action = "bijwerken" if f5_update else "downloaden"
        print(f"\n>>> Bezig met {action} van F5-TTS weights (SWivid/F5-TTS)...")
        try:
            download_model("f5_tts")
            print("[+] F5-TTS succesvol bijgewerkt!")
        except Exception as e:
            print(f"[!] Waarschuwing bij F5-TTS: {e}")

    # Download or update Stable Audio Open
    if not stable_present or stable_update:
        action = "bijwerken" if stable_update else "downloaden"
        print(f"\n>>> Bezig met {action} van Stable Audio Open 1.0 (stabilityai/stable-audio-open-1.0)...")
        try:
            download_model("stable_audio")
            print("[+] Stable Audio Open succesvol bijgewerkt!")
        except Exception as e:
            print(f"[!] Waarschuwing bij Stable Audio Open: {e}")

    print("\n" + "=" * 68)
    print("[OK] Modelverificatie en updates succesvol voltooid.")
    print("=" * 68 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(check_and_download_all())
