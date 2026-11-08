"""
Creates a GitHub release for XonAudio Studio and uploads the portable ZIP.
Usage: python scripts/create_github_release.py --token YOUR_GITHUB_TOKEN
Get a token at: https://github.com/settings/tokens (needs repo scope)
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO = "Xonarouss/xonaudiostudio"
TAG = "v1.3.0"
ZIP_PATH = BASE_DIR / "XonAudio-Studio-v1.3.0-Portable.zip"
UPLOAD_NAME = "XonAudio-Studio-v1.3.0-Portable.zip"

RELEASE_NOTES = """\
# 🎙️ XonAudio Studio v1.3.0
### Next-Gen Local AI Audio Workstation • AI Song Cover Lab • 3 Voice Engines • 3 SFX Engines
**Built with passion by [Xonarous Inc](https://xonarous.nl)**

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20x64-blue.svg?style=for-the-badge&logo=windows)](https://xonarous.nl)
[![CUDA](https://img.shields.io/badge/CUDA-12.8%2B%20%7C%20PyTorch%202.12-green.svg?style=for-the-badge&logo=nvidia)](https://xonarous.nl)
[![Architecture](https://img.shields.io/badge/Architecture-Blackwell%20sm__120%20%7C%20Ada%20%7C%20Ampere-purple.svg?style=for-the-badge)](https://xonarous.nl)
[![Dutch](https://img.shields.io/badge/🇳🇱%20Dutch%20TTS-Supported%20(XTTS%20+%20Fish)-orange.svg?style=for-the-badge)](https://xonarous.nl)

---

### 🚀 Major Highlights in v1.3.0

#### 1. 🎵 AI Song Cover Lab
- **Audio Ingestion:** Drag-and-drop song files (MP3/WAV/FLAC) or paste direct YouTube / Spotify URLs.
- **BS-RoFormer Vocal Isolation:** SOTA 12.97 SDR separation on CUDA via PyTorch Lightning to cleanly isolate singing vocals and backing instruments with zero bleed.
- **RVC v2 Neural Voice Conversion:** Deep neural voice conversion with RMVPE 100 FPS pitch extraction and pitch shifting (-12 to +12 semitones).
- **Bit-Exact pure-PyTorch HuBERT:** 100% bit-exact acoustic phonetic representation mapping with unvoiced consonant protection.
- **Dynamic Hi-Fi Stem Mixing:** Independent volume sliders (0–150%) with dynamic RMS envelope matching.
- **Studio Dual Export:** Broadcast-ready **320 kbps MP3** (FFmpeg libmp3lame) and **24-bit Lossless Studio Master WAV**.

#### 2. 🗃️ Generations Library Song Cover Archive
- All generated song cover full mixes, isolated vocals, and backing instrumentals are now automatically cataloged in the Generations Library.
- Dedicated **[Song Covers]** filter tab with waveform playback, MP3/WAV export, and deletion management.

#### 3. 🎛️ Triple SFX Diffusion Suite
- **Stable Audio 3 Medium DiT:** Stability AI's Diffusion Transformer with 10-step high-speed synthesis.
- **Stable Audio Open 1.0:** 44.1kHz stereo Foley and musical motifs.
- **AudioLDM 2 Studio:** Dual CLAP + T5 narrative sound effect synthesis designed for multi-event soundscapes.
- **Smart Negative Prompt Sanitization:** Automatically detects vocal/musical intent to prevent cancellation conflicts.

#### 4. 🗣️ 3-Engine Voice Lab with 🇳🇱 Dutch Support
- F5-TTS v1 Base, Coqui XTTS-v2, and Fish Speech 1.5 Ultra with studio Dutch presets (`daan_nl`, `femke_nl`, `bram_nl`, `lotte_nl`) and expressive laughter cues.

---

### 💻 How to Run
1. Download **`XonAudio-Studio-v1.3.0-Portable.zip`** below.
2. Extract the archive anywhere on your Windows PC.
3. Double-click **`Start_AudioStudio.bat`** (auto-verifies and downloads required models on first run).
4. Studio UI opens automatically at `http://localhost:5173`.

**Built by Xonarous Inc** • [https://xonarous.nl](https://xonarous.nl)
"""

def api_request(url, token, method="GET", data=None, content_type="application/json"):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        else:
            body = data
            req.add_header("Content-Type", content_type)
        req.data = body
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--delete-old", action="store_true", default=True, help="Delete older releases on GitHub")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: Provide --token or set GH_TOKEN env var.")
        print("Get a token at: https://github.com/settings/tokens (repo scope needed)")
        sys.exit(1)

    if not ZIP_PATH.exists():
        print(f"Release ZIP not found at {ZIP_PATH}. Building package...")
        import subprocess
        subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "build_release_zip.py")], check=True)

    token = args.token
    api_base = "https://api.github.com"

    # Delete older releases if requested
    if args.delete_old:
        print("[0/3] Checking and deleting older releases...")
        try:
            releases = api_request(f"{api_base}/repos/{REPO}/releases", token)
            for r in releases:
                if r.get("tag_name") != TAG:
                    r_id = r["id"]
                    r_tag = r.get("tag_name", "unknown")
                    print(f"    Deleting previous release {r_tag} (ID: {r_id})...")
                    try:
                        api_request(f"{api_base}/repos/{REPO}/releases/{r_id}", token, method="DELETE")
                        print(f"    ✓ Deleted release {r_tag}")
                    except Exception as del_err:
                        print(f"    ✗ Could not delete release {r_tag}: {del_err}")
                    
                    # Delete tag ref as well
                    try:
                        api_request(f"{api_base}/repos/{REPO}/git/refs/tags/{r_tag}", token, method="DELETE")
                        print(f"    ✓ Deleted tag ref {r_tag}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"    Warning checking previous releases: {e}")

    # 1. Create the release
    print(f"[1/3] Creating GitHub release {TAG}...")
    release_data = {
        "tag_name": TAG,
        "name": f"XonAudio Studio {TAG} — AI Song Cover Lab, BS-RoFormer, RVC v2 & Hi-Fi Dual Export",
        "body": RELEASE_NOTES,
        "draft": False,
        "prerelease": False,
    }
    try:
        release = api_request(f"{api_base}/repos/{REPO}/releases", token, "POST", release_data)
        upload_url = release["upload_url"].split("{")[0]
        release_id = release["id"]
        print(f"    Release created: {release['html_url']}")
    except Exception as e:
        print(f"    Release may already exist, trying to find it... ({e})")
        releases = api_request(f"{api_base}/repos/{REPO}/releases", token)
        existing = next((r for r in releases if r["tag_name"] == TAG), None)
        if not existing:
            print("ERROR: Could not create or find release.")
            sys.exit(1)
        upload_url = existing["upload_url"].split("{")[0]
        release_id = existing["id"]
        print(f"    Found existing release: {existing['html_url']}")

    # 2. Upload the ZIP asset
    print(f"[2/3] Uploading {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / 1024 / 1024:.1f} MB)...")
    with open(ZIP_PATH, "rb") as f:
        zip_data = f.read()
    upload_resp = api_request(
        f"{upload_url}?name={UPLOAD_NAME}&label=XonAudio+Studio+{TAG}+Portable+(Windows)",
        token, "POST", zip_data, "application/zip"
    )
    print(f"    Asset uploaded: {upload_resp.get('browser_download_url', 'OK')}")

    print(f"[3/3] Done! Release page: https://github.com/{REPO}/releases/tag/{TAG}")

if __name__ == "__main__":
    main()

