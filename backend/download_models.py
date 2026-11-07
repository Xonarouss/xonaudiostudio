import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from models_manager import is_f5_installed, is_stable_audio_installed, download_model, F5_DIR, STABLE_AUDIO_DIR

def check_and_download_all():
    print("=" * 65)
    print("          AI AUDIO STUDIO - MODEL VERIFICATIE")
    print("=" * 65)
    print(f"[*] Lokale modelmap: {F5_DIR.parent}")

    f5_present = is_f5_installed()
    stable_present = is_stable_audio_installed()

    if f5_present:
        print("[+] F5-TTS Checkpoint: AANWEZIG (Sla download over)")
    else:
        print("[-] F5-TTS Checkpoint: ONTBREEKT")

    if stable_present:
        print("[+] Stable Audio Open Checkpoint: AANWEZIG (Sla download over)")
    else:
        print("[-] Stable Audio Open Checkpoint: ONTBREEKT")

    if f5_present and stable_present:
        print("-" * 65)
        print("[OK] Alle benodigde weights zijn lokaal aanwezig!")
        print("[OK] Server wordt direct gestart zonder download-wachttijd.")
        print("=" * 65)
        return 0

    print("-" * 65)
    print("[!] Een of meerdere AI-modellen ontbreken. Download start nu...")
    print("[!] De voortgangsbalken van Hugging Face worden hieronder getoond.")
    print("-" * 65)

    if not f5_present:
        print("\n>>> Bezig met downloaden van F5-TTS weights (SWivid/F5-TTS)...")
        try:
            download_model("f5_tts")
            print("[+] F5-TTS download voltooid!")
        except Exception as e:
            print(f"[!] Waarschuwing bij F5-TTS download: {e}")
            print("[!] Je kunt dit model later ook downloaden via de Model Manager in de UI.")

    if not stable_present:
        print("\n>>> Bezig met downloaden van Stable Audio Open 1.0 (stabilityai/stable-audio-open-1.0)...")
        try:
            download_model("stable_audio")
            print("[+] Stable Audio Open download voltooid!")
        except Exception as e:
            print(f"[!] Waarschuwing bij Stable Audio Open download: {e}")
            print("[!] Je kunt dit model later ook downloaden via de Model Manager in de UI.")

    print("\n" + "=" * 65)
    print("[OK] Modelverificatie en downloadstap afgerond.")
    print("=" * 65 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(check_and_download_all())

