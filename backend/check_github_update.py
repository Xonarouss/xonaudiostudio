import os
import sys
import subprocess
import json
import urllib.request
from pathlib import Path

REPO = "Xonarouss/xonaudiostudio"
CURRENT_VERSION = "v1.0.0"
BASE_DIR = Path(__file__).resolve().parent.parent

def check_and_update():
    print("=" * 68)
    print("        XONAUDIO STUDIO - GITHUB AUTO-UPDATE CHECK")
    print(f"        Repository: https://github.com/{REPO}")
    print("=" * 68)

    # 1. If inside a git repository, check for upstream git commits
    git_dir = BASE_DIR / ".git"
    if git_dir.exists():
        try:
            print("[*] Checking git repository for upstream updates...")
            # Fetch silently
            res = subprocess.run(["git", "fetch", "--quiet"], cwd=str(BASE_DIR), capture_output=True, timeout=8)
            if res.returncode == 0:
                # Compare HEAD with upstream
                local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
                try:
                    upstream_hash = subprocess.check_output(["git", "rev-parse", "@{u}"], cwd=str(BASE_DIR), text=True).strip()
                    if local_hash != upstream_hash:
                        print("[!] New update found on GitHub repository! Pulling latest changes...")
                        pull_res = subprocess.run(["git", "pull", "--quiet"], cwd=str(BASE_DIR), text=True)
                        if pull_res.returncode == 0:
                            print("[+] Successfully updated XonAudio Studio to the latest commit!")
                            return 0
                        else:
                            print("[!] Git pull encountered a merge conflict or warning. Continuing with local files...")
                    else:
                        print("[+] Local installation is up-to-date with GitHub repository.")
                except Exception:
                    # Upstream tracking branch not set yet
                    pass
        except Exception as e:
            print(f"[*] Git check skipped: {e}")

    # 2. Check GitHub Releases API
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "XonAudio-Studio-Client"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                latest_tag = data.get("tag_name", "")
                if latest_tag and latest_tag != CURRENT_VERSION:
                    print(f"[!] New Release Available: {latest_tag} (Current: {CURRENT_VERSION})")
                    print(f"[*] Release Notes: {data.get('name', 'Latest Release')}")
                    print(f"[*] Download at: https://github.com/{REPO}/releases/latest")
                else:
                    print(f"[+] Version check: You are running the latest release ({CURRENT_VERSION}).")
    except Exception:
        # Offline or repo is private / rate limited
        print("[*] GitHub release check completed (offline/current).")

    print("=" * 68 + "\n")
    return 0

if __name__ == "__main__":
    check_and_update()

