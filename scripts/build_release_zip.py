import os
import zipfile
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_ZIP = ROOT_DIR / "XonAudio-Studio-v1.2.0-Portable.zip"

def build_frontend():
    print("[1/3] Building frontend production bundle...")
    frontend_dir = ROOT_DIR / "frontend"
    try:
        subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), shell=True, check=True)
        print("[+] Frontend built successfully in frontend/dist!")
    except Exception as e:
        print(f"[!] Warning: Could not run npm build: {e}")

def create_zip():
    print("[2/3] Creating standalone release package...")
    if DIST_ZIP.exists():
        DIST_ZIP.unlink()

    # Paths and folders to include
    include_paths = [
        "Start_AudioStudio.bat",
        "Install_Environment.bat",
        "start_audiostudio.sh",
        "README.md",
        "LICENSE",
        ".env.example",
        "backend",
        "frontend/dist",
        "frontend/package.json",
        "assets",
        "docs",
        "scripts",
        "models/f5-tts/.gitkeep",
        "models/stable-audio-open/.gitkeep",
        "models/llama/.gitkeep",
        "models/xtts-v2/.gitkeep",
        "models/fish-speech-1.5/.gitkeep",
        "outputs/tts/.gitkeep",
        "outputs/sfx/.gitkeep",
    ]

    # Exclusions
    exclude_patterns = [
        "__pycache__",
        ".pyc",
        "venv",
        "node_modules",
        ".git",
        ".version_cache.json"
    ]

    total_files = 0
    with zipfile.ZipFile(DIST_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for rel_path in include_paths:
            full_path = ROOT_DIR / rel_path
            if not full_path.exists():
                continue

            if full_path.is_file():
                arcname = f"XonAudio-Studio/{rel_path}"
                zipf.write(full_path, arcname)
                total_files += 1
            elif full_path.is_dir():
                for root, dirs, files in os.walk(full_path):
                    # Filter out excluded dirs
                    dirs[:] = [d for d in dirs if not any(ex in d for ex in exclude_patterns)]
                    for f in files:
                        if any(ex in f for ex in exclude_patterns):
                            continue
                        file_full = Path(root) / f
                        arcname = f"XonAudio-Studio/{file_full.relative_to(ROOT_DIR)}"
                        zipf.write(file_full, arcname)
                        total_files += 1

    zip_size_mb = DIST_ZIP.stat().st_size / (1024 * 1024)
    print(f"[3/3] Standalone release zip created:")
    print(f"      File: {DIST_ZIP}")
    print(f"      Size: {zip_size_mb:.2f} MB ({total_files} files)")
    print(f"\n[+] Ready for GitHub Releases upload!")

if __name__ == "__main__":
    build_frontend()
    create_zip()

