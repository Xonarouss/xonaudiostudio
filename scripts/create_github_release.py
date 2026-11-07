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
TAG = "v1.1.0"
ZIP_PATH = BASE_DIR / "XonAudio-Studio-v1.0.0-Portable.zip"
UPLOAD_NAME = "XonAudio-Studio-v1.1.0-Portable.zip"

RELEASE_NOTES = """\
## XonAudio Studio v1.1.0

### New Features
- **Emotion/Style Direction Panel** — 10 emotion presets (Angry, Fearful, Sad, Happy, Whisper, Loud, Sarcastic, Calm, Excited, Neutral) prepended as natural language stage cues to your TTS prompt
- **Language Selector** — English, Chinese Mandarin, and Auto-detect support in Voice Lab
- **Distinct Aria Voice** — Aria now uses a real female voice sample (Chinese F5-TTS reference), clearly different from Atlas and Default
- **Custom Voice MP3 Support** — Uploaded MP3 voices now stream with the correct audio/mpeg MIME type

### Bug Fixes
- **Sound Studio blank white page** — Fixed undefined `isStableAudioReady` variable causing React crash
- **AI Assistant 'Not Installed' banner** — Fixed race condition; banner no longer flashes when model is already loaded
- **Llama attention_mask** — Added proper attention_mask passthrough to suppress generation warnings and improve output quality
- **ref_text 'Hello there' fallback** — Removed hard-coded fallback that caused random words in output; now uses F5-TTS built-in ASR auto-transcription
- **Aria/Atlas voice distinction** — All 3 preset voices (Aria, Atlas, Default) were previously identical; Aria is now a distinct female voice

### How to Run
1. Extract the ZIP
2. Double-click **Start_AudioStudio.bat** (auto-installs all models on first run)
3. Open http://127.0.0.1:8000 in your browser

**Requirements:** Windows 10/11, NVIDIA GPU (RTX recommended), Python 3.10+
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

