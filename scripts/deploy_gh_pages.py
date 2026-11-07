import os
import stat
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def deploy():
    print("[1/4] Preparing gh-pages package from docs/...")
    temp_dir = Path(tempfile.gettempdir()) / "xonaudio_gh_pages"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, onerror=on_rm_error)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files from docs to temp_dir
    for item in DOCS_DIR.iterdir():
        dest = temp_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Add .nojekyll to prevent GitHub from ignoring files with underscores
    (temp_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"[+] Files staged in {temp_dir}")

    print("[2/4] Initializing git repository on gh-pages branch...")
    subprocess.run(["git", "init", "-b", "gh-pages"], cwd=str(temp_dir), check=True)
    subprocess.run(["git", "add", "."], cwd=str(temp_dir), check=True)
    subprocess.run(["git", "commit", "-m", "Deploy modern responsive GitHub Pages website with real audio samples"], cwd=str(temp_dir), check=True)

    print("[3/4] Adding origin remote...")
    remote_url = "https://github.com/Xonarouss/xonaudiostudio.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=str(temp_dir), check=True)

    print("[4/4] Pushing to origin gh-pages...")
    subprocess.run(["git", "push", "origin", "gh-pages", "--force"], cwd=str(temp_dir), check=True)
    print("\n[SUCCESS] gh-pages branch successfully pushed to GitHub!")
    print("GitHub Pages will now automatically deploy the website at:")
    print("https://xonarouss.github.io/xonaudiostudio/")

if __name__ == "__main__":
    deploy()
