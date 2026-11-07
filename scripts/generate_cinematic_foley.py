import numpy as np
import soundfile as sf
import scipy.signal as signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT_DIR / "docs" / "assets" / "foley_sample.wav"

def generate_cinema_foley():
    sr = 44100
    duration = 6.0
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    print("[*] Synthesizing Hollywood-grade cinematic rain & thunder foley...")

    # ==========================================
    # 1. LAYER 1: BINAURAL STEREO RAIN PATTER
    # ==========================================
    # Generate pink noise (1/f) using Voss-McCartney approximation
    num_rows = 16
    array = np.random.randn(num_rows, n // num_rows + 1)
    array = np.repeat(array, num_rows, axis=1)[:, :n]
    pink_base = np.sum(array, axis=0)
    pink_base = pink_base / np.max(np.abs(pink_base))

    # Decorrelate for Left and Right channels (subtle delay & distinct micro noise)
    noise_l = pink_base + np.random.normal(0, 0.15, n)
    noise_r = np.roll(pink_base, int(sr * 0.003)) + np.random.normal(0, 0.15, n)

    # Bandpass filter for gentle rain (200 Hz to 4500 Hz, butterworth order 3)
    sos_rain = signal.butter(3, [250, 4500], btype='bandpass', fs=sr, output='sos')
    rain_l = signal.sosfilt(sos_rain, noise_l) * 0.22
    rain_r = signal.sosfilt(sos_rain, noise_r) * 0.22

    # High frequency glass window droplet sheen (5 kHz to 12 kHz)
    sos_droplets = signal.butter(2, 5200, btype='highpass', fs=sr, output='sos')
    sheen_l = signal.sosfilt(sos_droplets, np.random.randn(n)) * 0.04
    sheen_r = signal.sosfilt(sos_droplets, np.random.randn(n)) * 0.04

    # Add discrete water drops (micro acoustic droplet impacts)
    rng = np.random.default_rng(42)
    for _ in range(160):
        pos = rng.integers(0, n - 400)
        pan = rng.uniform(0.1, 0.9)
        decay = np.exp(-np.linspace(0, 18, 300))
        freq = rng.uniform(1800, 3200)
        drop_wav = np.sin(2 * np.pi * freq * np.linspace(0, 0.007, 300)) * decay * rng.uniform(0.04, 0.14)
        rain_l[pos:pos+300] += drop_wav * (1.0 - pan)
        rain_r[pos:pos+300] += drop_wav * pan

    rain_stereo_l = rain_l + sheen_l
    rain_stereo_r = rain_r + sheen_r

    # ==========================================
    # 2. LAYER 2: CINEMATIC TRAILER THUNDER
    # ==========================================
    # Lightning crack transient at t = 1.0s
    crack_start = int(sr * 1.0)
    crack_len = int(sr * 0.15)
    crack_t = np.linspace(0, 0.15, crack_len)
    crack_noise = np.random.randn(crack_len) * np.exp(-35 * crack_t) * 0.45
    sos_crack = signal.butter(2, [300, 3500], btype='bandpass', fs=sr, output='sos')
    crack_filtered = signal.sosfilt(sos_crack, crack_noise)

    # Deep sub-bass acoustic rumble starting t = 1.05s, sustaining across 4.5 seconds
    rumble_start = int(sr * 1.02)
    rumble_len = n - rumble_start
    rumble_t = np.linspace(0, duration - 1.02, rumble_len)

    # Natural acoustic swell and long cavernous decay envelope
    envelope = (rumble_t ** 0.8) * np.exp(-0.75 * rumble_t)
    envelope = envelope / np.max(envelope)

    # Multi-frequency sub-bass harmonics (42Hz, 58Hz, 84Hz, 116Hz)
    sub42 = np.sin(2 * np.pi * 42.0 * rumble_t + 0.3 * np.sin(2 * np.pi * 1.5 * rumble_t))
    sub58 = np.sin(2 * np.pi * 58.0 * rumble_t + 0.2 * np.sin(2 * np.pi * 2.1 * rumble_t)) * 0.7
    sub84 = np.sin(2 * np.pi * 84.0 * rumble_t) * 0.4
    rumble_noise = signal.sosfilt(
        signal.butter(3, 160, btype='lowpass', fs=sr, output='sos'),
        np.random.randn(rumble_len)
    ) * 0.65

    thunder_core = (sub42 + sub58 + sub84 + rumble_noise) * envelope * 0.65

    # Stereo dispersal of thunder (binaural room reflections)
    thunder_l = np.zeros(n)
    thunder_r = np.zeros(n)

    # Place crack
    thunder_l[crack_start:crack_start+crack_len] += crack_filtered * 0.8
    thunder_r[crack_start:crack_start+crack_len] += crack_filtered * 0.7

    # Place rolling rumble with slight delay between ears
    thunder_l[rumble_start:n] += thunder_core * 0.95
    del_samples = int(sr * 0.015) # 15ms Haas delay for massive width
    thunder_r[rumble_start + del_samples:n] += thunder_core[:-del_samples] * 1.02

    # ==========================================
    # 3. MASTERING & EQUALIZATION
    # ==========================================
    # Gentle fade in / fade out to eliminate any clicks
    fade_len = int(sr * 0.05)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)

    mix_l = rain_stereo_l + thunder_l
    mix_r = rain_stereo_r + thunder_r

    mix_l[:fade_len] *= fade_in
    mix_l[-fade_len:] *= fade_out
    mix_r[:fade_len] *= fade_in
    mix_r[-fade_len:] *= fade_out

    # Professional limiting & peak normalization to -0.5 dBFS
    stereo = np.column_stack((mix_l, mix_r))
    peak = np.max(np.abs(stereo))
    if peak > 0:
        target_peak = 10 ** (-0.5 / 20) # ~0.944
        stereo = stereo * (target_peak / peak)

    sf.write(str(OUT_PATH), stereo.astype(np.float32), sr, subtype='PCM_24')
    print(f"[+] Studio-grade Foley sample rendered: {OUT_PATH}")
    print(f"    Duration: {duration:.2f}s | Channels: 2 (Stereo) | 24-bit PCM {sr}Hz | Peak: -0.5 dBFS")

if __name__ == "__main__":
    generate_cinema_foley()
