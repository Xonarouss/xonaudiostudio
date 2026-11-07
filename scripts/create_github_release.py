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
TAG = "v1.2.0"
ZIP_PATH = BASE_DIR / "XonAudio-Studio-v1.2.0-Portable.zip"
UPLOAD_NAME = "XonAudio-Studio-v1.2.0-Portable.zip"

RELEASE_NOTES = """\
# 🎙️ XonAudio Studio v1.2.0

### 🚀 Major Highlights

#### 1. Three Neural Voice Engines (Voice Lab Switcher)
- **F5-TTS v1 Base** — Flow-matching non-autoregressive diffusion with fast ODE solver (English & Chinese Mandarin zero-shot voice cloning).
- **Coqui XTTS-v2** — SOTA multilingual voice cloning across 17 languages with native **Dutch (Nederlands 🇳🇱)**, German, French, Spanish, Italian, Portuguese, and more.
- **Fish Speech 1.5 Ultra** — The newest dual autoregressive (DAR) + VQ-GAN neural audio codec architecture. 100% fully local, ultra-natural cadence, zero cloud/API dependencies, with native **Dutch (🇳🇱)** support.

#### 2. 🇳🇱 Native Dutch Language Support
- Full high-fidelity Dutch speech synthesis and voice cloning via XTTS-v2 and Fish Speech 1.5.

#### 3. Automatic Dependency & FFmpeg Installer
- `Start_AudioStudio.bat` and `Install_Environment.bat` now automatically check and install all required audio processing packages (`torchsde`, `einops`, `encodec`, `pydub`, `phonemizer`, `imageio-ffmpeg`).
- Automatically bundles and links static `ffmpeg.exe` binaries directly into `venv\Scripts\ffmpeg.exe` so pydub and torchaudio have zero configuration overhead.

#### 4. Magic Wand & Llama Prompt Enhancer Fix
- Fixed `enhance_prompt()` to automatically load Llama 3 on demand when installed.
- Expanded `max_new_tokens` to 200 for rich cinematic acoustic descriptions.

#### 5. Aria Voice & Preset Audio Refinements
- Replaced Aria voice sample with a natural female English narration voice.
- Set auto-ASR transcription for zero pronunciation artifacts.

#### 6. Website Update
- Dedicated **5 Neural AI Architectures** showcase live on GitHub Pages with model specs, VRAM footprints, and Dutch language badges.

---

### 💻 How to Run
1. Download **`XonAudio-Studio-v1.2.0-Portable.zip`**
2. Extract the archive
3. Double-click **`Start_AudioStudio.bat`** (auto-installs all requirements on first run)
4. Studio UI opens automatically at `http://localhost:5173`

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
    args = parser.parse_args()

    if not args.token:
        print("ERROR: Provide --token or set GH_TOKEN env var.")
        print("Get a token at: https://github.com/settings/tokens (repo scope needed)")
        sys.exit(1)

    if not ZIP_PATH.exists():
        print(f"ERROR: Release ZIP not found at {ZIP_PATH}")
        print("Run: python scripts/build_release_zip.py")
        sys.exit(1)

    token = args.token
    api_base = "https://api.github.com"

    # 1. Create the release
    print(f"[1/3] Creating GitHub release {TAG}...")
    release_data = {
        "tag_name": TAG,
        "name": f"XonAudio Studio {TAG} — Emotion Control, Voice Library & AI Fixes",
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
        f"{upload_url}?name={UPLOAD_NAME}&label=XonAudio+Studio+v1.1.0+Portable+(Windows)",
        token, "POST", zip_data, "application/zip"
    )
    print(f"    Asset uploaded: {upload_resp.get('browser_download_url', 'OK')}")

    print(f"[3/3] Done! Release page: https://github.com/{REPO}/releases/tag/{TAG}")

if __name__ == "__main__":
    main()

