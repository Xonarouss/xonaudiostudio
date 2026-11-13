import os
from pathlib import Path

out_dir = Path("frontend/public/avatars")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Avatar Chris (Sound Engineer with Headphones & Soundwave)
chris_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="100%" height="100%">
  <defs>
    <linearGradient id="gradChris" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="50%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#8b5cf6" />
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#d97706" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="36" fill="#0f172a" />
  <rect x="3" y="3" width="122" height="122" rx="33" fill="none" stroke="url(#gradChris)" stroke-width="2.5" opacity="0.7" />
  <!-- Studio Engineer Silhouette -->
  <circle cx="64" cy="50" r="22" fill="url(#gradChris)" />
  <!-- Shades -->
  <rect x="48" y="45" width="32" height="10" rx="5" fill="#0f172a" />
  <rect x="50" y="47" width="28" height="6" rx="3" fill="#38bdf8" opacity="0.9" />
  <!-- Over-Ear Studio Headphones -->
  <path d="M 36 52 A 28 28 0 0 1 92 52" fill="none" stroke="#e2e8f0" stroke-width="5" stroke-linecap="round" />
  <rect x="30" y="44" width="10" height="18" rx="5" fill="url(#goldGrad)" />
  <rect x="88" y="44" width="10" height="18" rx="5" fill="url(#goldGrad)" />
  <!-- Shoulders -->
  <path d="M 26 108 C 26 84, 42 76, 64 76 C 86 76, 102 84, 102 108 Z" fill="url(#gradChris)" opacity="0.9" />
  <!-- Soundwave Bars -->
  <rect x="56" y="86" width="3" height="12" rx="1.5" fill="#ffffff" />
  <rect x="62.5" y="82" width="3" height="18" rx="1.5" fill="#ffffff" />
  <rect x="69" y="86" width="3" height="12" rx="1.5" fill="#ffffff" />
</svg>"""
(out_dir / "avatar-chris.svg").write_text(chris_svg, encoding="utf-8")
print("[+] Created avatar-chris.svg")

# 2. Avatar Studio
studio_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="100%" height="100%">
  <defs>
    <linearGradient id="gradStudio" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ec4899" />
      <stop offset="100%" stop-color="#8b5cf6" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="36" fill="#0f172a" />
  <rect x="3" y="3" width="122" height="122" rx="33" fill="none" stroke="url(#gradStudio)" stroke-width="2.5" opacity="0.7" />
  <rect x="50" y="28" width="28" height="44" rx="14" fill="url(#gradStudio)" />
  <path d="M 38 56 C 38 74, 90 74, 90 56" fill="none" stroke="#f8fafc" stroke-width="4" stroke-linecap="round" />
  <line x1="64" y1="76" x2="64" y2="96" stroke="#f8fafc" stroke-width="4" stroke-linecap="round" />
  <line x1="48" y1="96" x2="80" y2="96" stroke="#f8fafc" stroke-width="4" stroke-linecap="round" />
</svg>"""
(out_dir / "avatar-studio.svg").write_text(studio_svg, encoding="utf-8")
print("[+] Created avatar-studio.svg")

# 3. Avatar Neon Pulse
neon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="100%" height="100%">
  <defs>
    <linearGradient id="gradNeon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#06b6d4" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="36" fill="#022c22" />
  <rect x="3" y="3" width="122" height="122" rx="33" fill="none" stroke="url(#gradNeon)" stroke-width="2.5" opacity="0.7" />
  <circle cx="64" cy="64" r="34" fill="none" stroke="url(#gradNeon)" stroke-width="3" stroke-dasharray="6 4" />
  <path d="M 34 64 L 46 64 L 54 44 L 64 84 L 74 50 L 82 64 L 94 64" fill="none" stroke="#34d399" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
</svg>"""
(out_dir / "avatar-neon.svg").write_text(neon_svg, encoding="utf-8")
print("[+] Created avatar-neon.svg")

# 4. Avatar Producer
producer_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="100%" height="100%">
  <defs>
    <linearGradient id="gradProd" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#ef4444" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="36" fill="#1c1917" />
  <rect x="3" y="3" width="122" height="122" rx="33" fill="none" stroke="url(#gradProd)" stroke-width="2.5" opacity="0.7" />
  <circle cx="64" cy="64" r="38" fill="#0c0a09" stroke="#44403c" stroke-width="3" />
  <circle cx="64" cy="64" r="26" fill="none" stroke="#292524" stroke-width="1.5" />
  <circle cx="64" cy="64" r="16" fill="url(#gradProd)" />
  <circle cx="64" cy="64" r="5" fill="#f8fafc" />
</svg>"""
(out_dir / "avatar-producer.svg").write_text(producer_svg, encoding="utf-8")
print("[+] Created avatar-producer.svg")
