import numpy as np
import soundfile as sf
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT_DIR / "docs" / "assets" / "foley_sample.wav"

def generate_foley():
    sr = 44100
    duration = 5.0
    num_samples = int(sr * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # 1. Binaural Rain Texture (filtered noise with slight stereo delay)
    noise_l = np.random.normal(0, 0.05, num_samples)
    noise_r = np.random.normal(0, 0.05, num_samples)

    # Simple moving average / low-pass for rain patter
    kernel_size = 12
    kernel = np.ones(kernel_size) / kernel_size
    rain_l = np.convolve(noise_l, kernel, mode='same')
    rain_r = np.convolve(noise_r, kernel, mode='same')

    # Add micro droplets (occasional sharp ticks)
    for _ in range(80):
        pos = np.random.randint(0, num_samples - 200)
        pan = np.random.uniform(0.2, 0.8)
        drop = np.sin(np.linspace(0, np.pi * 4, 150)) * np.exp(-np.linspace(0, 8, 150)) * 0.12
        rain_l[pos:pos+150] += drop * (1 - pan)
        rain_r[pos:pos+150] += drop * pan

    # 2. Distant Cinematic Rolling Thunder (Deep resonant rumble at t=1.2s to 4.5s)
    thunder_t = np.maximum(0, t - 1.2)
    thunder_env = np.exp(-1.2 * thunder_t) * (thunder_t > 0)
    # Modulation
    sub_freq = 55.0 + 15.0 * np.sin(2 * np.pi * 0.8 * thunder_t)
    thunder_wave = np.sin(2 * np.pi * sub_freq * thunder_t) * thunder_env * 0.35
    # Add rumble harmonics
    thunder_wave += np.sin(2 * np.pi * 82.0 * thunder_t) * thunder_env * 0.15
    thunder_wave += np.random.normal(0, 0.08, num_samples) * thunder_env

    # 3. Combine Stereo
    left = rain_l + thunder_wave * 0.95
    right = rain_r + thunder_wave * 1.05

    # Normalize to -1 dB
    stereo = np.column_stack((left, right))
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = (stereo / max_val) * 0.85

    sf.write(str(OUT_PATH), stereo.astype(np.float32), sr)
    print(f"[+] Foley sample created: {OUT_PATH} ({len(stereo)/sr:.2f}s, {sr}Hz stereo)")

if __name__ == "__main__":
    generate_foley()

