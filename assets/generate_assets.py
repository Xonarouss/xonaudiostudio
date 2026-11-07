import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = Path(__file__).resolve().parent

# 1. Create SVG
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <!-- Background Gradients -->
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#111827" />
      <stop offset="100%" stop-color="#030712" />
    </radialGradient>
    <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="50%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#8b5cf6" />
    </linearGradient>
    <linearGradient id="purplePink" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#ec4899" />
    </linearGradient>
    <!-- Glow Filters -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="12" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <!-- Squircle Base Frame -->
  <rect x="24" y="24" width="464" height="464" rx="104" fill="url(#bgGlow)" stroke="#1e293b" stroke-width="6" />
  <rect x="28" y="28" width="456" height="456" rx="100" fill="none" stroke="url(#neonGradient)" stroke-width="2" opacity="0.6" />

  <!-- Abstract Glowing 'X' Soundwaves -->
  <g filter="url(#glow)">
    <!-- Diagonal 1: Cyan to Purple -->
    <path d="M 120 120 C 200 200, 220 220, 256 256 C 292 292, 312 312, 392 392" 
          stroke="url(#neonGradient)" stroke-width="32" stroke-linecap="round" fill="none" />
    <!-- Diagonal 2: Purple to Pink -->
    <path d="M 392 120 C 312 200, 292 220, 256 256 C 220 292, 200 312, 120 392" 
          stroke="url(#purplePink)" stroke-width="32" stroke-linecap="round" fill="none" />

    <!-- Pulsating Studio Equalizer Bars (Vertical Nodes) -->
    <!-- Center Bar -->
    <rect x="244" y="160" width="24" height="192" rx="12" fill="#ffffff" />
    <!-- Left Bar 1 -->
    <rect x="194" y="196" width="20" height="120" rx="10" fill="#06b6d4" />
    <!-- Left Bar 2 -->
    <rect x="148" y="226" width="16" height="60" rx="8" fill="#06b6d4" opacity="0.8" />
    <!-- Right Bar 1 -->
    <rect x="298" y="196" width="20" height="120" rx="10" fill="#8b5cf6" />
    <!-- Right Bar 2 -->
    <rect x="348" y="226" width="16" height="60" rx="8" fill="#ec4899" opacity="0.8" />

    <!-- Center Energy Node Core -->
    <circle cx="256" cy="256" r="18" fill="#ffffff" />
  </g>
</svg>
"""

with open(ASSETS_DIR / "logo.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("[+] Created assets/logo.svg")

# 2. Render high quality PNG and multi-size Windows .ICO using Pillow
size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Squircle background
bg_margin = 24
draw.rounded_rectangle(
    [bg_margin, bg_margin, size - bg_margin, size - bg_margin],
    radius=100,
    fill=(10, 15, 26, 255),
    outline=(6, 182, 212, 200),
    width=6
)

# Gradient simulation for soundwave bars & stylized X
# Draw vertical studio bars with neon glow
bars = [
    (150, 230, 282, (6, 182, 212)),
    (196, 200, 312, (14, 165, 233)),
    (244, 156, 356, (255, 255, 255)),  # Center high bar
    (296, 200, 312, (139, 92, 246)),
    (346, 230, 282, (236, 72, 153))
]

# Draw glowing X lines behind bars
for i in range(120, 393, 4):
    t = (i - 120) / (392 - 120)
    # Color interpolation
    r = int(6 + t * (139 - 6))
    g = int(182 + t * (92 - 182))
    b = int(212 + t * (246 - 212))
    draw.ellipse([i - 8, i - 8, i + 8, i + 8], fill=(r, g, b, 140))
    draw.ellipse([512 - i - 8, i - 8, 512 - i + 8, i + 8], fill=(r, g, b, 140))

for x, y1, y2, color in bars:
    # Outer glow
    w = 20 if x != 244 else 24
    draw.rounded_rectangle([x - 3, y1 - 3, x + w + 3, y2 + 3], radius=12, fill=(*color, 80))
    # Core solid bar
    draw.rounded_rectangle([x, y1, x + w, y2], radius=10, fill=(*color, 255))

# Save PNG
png_path = ASSETS_DIR / "logo.png"
img.save(png_path, format="PNG")
print(f"[+] Created {png_path}")

# Save Multi-size Windows .ICO
ico_path = ASSETS_DIR / "icon.ico"
img.save(
    ico_path,
    format="ICO",
    sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
)
print(f"[+] Created {ico_path}")

# Copy to frontend/public for browser favicon
frontend_favicon = ASSETS_DIR.parent / "frontend" / "public" / "favicon.ico"
if frontend_favicon.parent.exists():
    img.save(frontend_favicon, format="ICO", sizes=[(32, 32), (16, 16)])
    print(f"[+] Updated frontend favicon: {frontend_favicon}")

