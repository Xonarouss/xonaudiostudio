import numpy as np
import soundfile as sf
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WAV_PATH = ROOT_DIR / "docs" / "assets" / "song_cover_temp.wav"
MP3_PATH = ROOT_DIR / "docs" / "assets" / "song_cover_sample.mp3"

def make_song_cover():
    sr = 44100
    duration = 16.0  # 16 seconds melodic demo
    num_samples = int(sr * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # Tempo: 110 BPM -> 1 beat = 60 / 110 = 0.5454s, 1 bar (4 beats) = 2.1818s
    beat_dur = 60.0 / 110.0
    bar_dur = beat_dur * 4

    # Chord progression: C (C4, E4, G4) -> G (G3, B3, D4) -> Am (A3, C4, E4) -> F (F3, A3, C4)
    # Frequencies (Hz)
    chords = [
        # C major: C3(130.81), C4(261.63), E4(329.63), G4(392.00)
        {"root": 130.81, "notes": [261.63, 329.63, 392.00, 523.25]},
        # G major: G2(98.00), G3(196.00), B3(246.94), D4(293.66)
        {"root": 98.00, "notes": [196.00, 246.94, 293.66, 392.00]},
        # A minor: A2(110.00), A3(220.00), C4(261.63), E4(329.63)
        {"root": 110.00, "notes": [220.00, 261.63, 329.63, 440.00]},
        # F major: F2(87.31), F3(174.61), A3(220.00), C4(261.63)
        {"root": 87.31, "notes": [174.61, 220.00, 261.63, 349.23]},
    ]

    left = np.zeros(num_samples, dtype=np.float32)
    right = np.zeros(num_samples, dtype=np.float32)

    # 1. Acoustic Arpeggiated Guitar / Piano Chords
    for bar_idx in range(int(duration / bar_dur) + 1):
        bar_start = bar_idx * bar_dur
        chord = chords[bar_idx % len(chords)]
        root = chord["root"]
        notes = chord["notes"]

        # Bass root note on beat 1 & 3
        for beat_offset in [0, beat_dur * 2]:
            note_time = bar_start + beat_offset
            if note_time >= duration:
                break
            idx_start = int(note_time * sr)
            len_note = min(int(beat_dur * 2.2 * sr), num_samples - idx_start)
            if len_note <= 0:
                continue
            sub_t = np.linspace(0, len_note / sr, len_note, endpoint=False)
            env = np.exp(-2.5 * sub_t) * (1.0 - np.exp(-30.0 * sub_t))
            bass_wave = (np.sin(2 * np.pi * root * sub_t) + 0.3 * np.sin(2 * np.pi * root * 2 * sub_t)) * env * 0.35
            left[idx_start:idx_start+len_note] += bass_wave * 0.8
            right[idx_start:idx_start+len_note] += bass_wave * 0.8

        # 8th note arpeggios (8 notes per bar)
        for arp_i in range(8):
            note_time = bar_start + arp_i * (beat_dur / 2.0)
            if note_time >= duration:
                break
            note_freq = notes[arp_i % len(notes)]
            idx_start = int(note_time * sr)
            len_note = min(int(0.8 * sr), num_samples - idx_start)
            if len_note <= 0:
                continue
            sub_t = np.linspace(0, len_note / sr, len_note, endpoint=False)
            env = np.exp(-4.0 * sub_t) * (1.0 - np.exp(-80.0 * sub_t))
            # Pluck timbre (harmonics)
            pluck = (
                np.sin(2 * np.pi * note_freq * sub_t) * 0.5 +
                np.sin(2 * np.pi * note_freq * 2 * sub_t) * 0.25 +
                np.sin(2 * np.pi * note_freq * 3 * sub_t) * 0.12 +
                np.sin(2 * np.pi * note_freq * 4 * sub_t) * 0.05
            ) * env * 0.22
            # Stereo pan alternating slightly
            pan = 0.35 + 0.3 * (arp_i % 2)
            left[idx_start:idx_start+len_note] += pluck * (1.0 - pan)
            right[idx_start:idx_start+len_note] += pluck * pan

    # 2. Neural Singing Lead Vocal Melody (Warm Formant Lead with Vibrato)
    # Melodic singing phrase: E4, G4, A4, G4, E4, D4, C4...
    melody_notes = [
        (0.5, 1.2, 329.63),   # E4
        (1.8, 0.9, 392.00),   # G4
        (2.8, 1.4, 440.00),   # A4
        (4.3, 1.2, 392.00),   # G4
        (5.6, 1.0, 329.63),   # E4
        (6.8, 1.8, 293.66),   # D4
        (8.8, 1.2, 329.63),   # E4
        (10.1, 1.0, 392.00),  # G4
        (11.2, 1.6, 440.00),  # A4
        (13.0, 2.5, 523.25),  # C5 (high resolving note)
    ]

    for start_s, dur_s, pitch_hz in melody_notes:
        if start_s >= duration:
            break
        idx_start = int(start_s * sr)
        len_lead = min(int(dur_s * sr), num_samples - idx_start)
        if len_lead <= 0:
            continue
        sub_t = np.linspace(0, len_lead / sr, len_lead, endpoint=False)
        # Singing attack and release envelope
        attack = np.minimum(1.0, sub_t / 0.08)
        decay = np.minimum(1.0, (len_lead / sr - sub_t) / 0.15)
        env = attack * decay

        # Natural vocal vibrato (starts after 0.2s of note)
        vib_depth = 4.5 * np.maximum(0.0, np.minimum(1.0, (sub_t - 0.2) / 0.3))
        vibrato = vib_depth * np.sin(2 * np.pi * 5.5 * sub_t)
        instant_f = pitch_hz + vibrato
        phase = np.cumsum(2 * np.pi * instant_f / sr)

        # Vocal Formant Simulation (fundamental + warm 2nd, 3rd, 4th, 5th harmonics)
        vocal_wave = (
            np.sin(phase) * 0.45 +
            np.sin(2 * phase) * 0.28 +
            np.sin(3 * phase) * 0.18 +
            np.sin(4 * phase) * 0.08 +
            np.sin(5 * phase) * 0.04
        ) * env * 0.38

        # Subtle stereo widening for lead vocal
        left[idx_start:idx_start+len_lead] += vocal_wave * 0.95
        right[idx_start:idx_start+len_lead] += vocal_wave * 1.05

    # 3. Soft Ambient Reverb Space
    reverb_delay = int(0.065 * sr)
    if num_samples > reverb_delay:
        left[reverb_delay:] += right[:-reverb_delay] * 0.22
        right[reverb_delay:] += left[:-reverb_delay] * 0.22

    # Fade-in (0.5s) and Fade-out (1.5s)
    fade_in_len = int(0.5 * sr)
    fade_out_len = int(1.5 * sr)
    left[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    right[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    left[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)
    right[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)

    # 4. Master Peak Limiting / Normalization (-1.0 dBFS)
    stereo = np.column_stack((left, right))
    peak = np.max(np.abs(stereo))
    if peak > 0:
        stereo = (stereo / peak) * 0.89

    # Save lossless temp WAV
    sf.write(str(WAV_PATH), stereo.astype(np.float32), sr)
    print(f"[+] Temp WAV created: {WAV_PATH} ({len(stereo)/sr:.1f}s)")

    # 5. Convert to 320 kbps High-Fidelity MP3 via FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(WAV_PATH),
        "-codec:a", "libmp3lame",
        "-b:a", "320k",
        "-ar", "44100",
        "-ac", "2",
        str(MP3_PATH)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[!] FFmpeg error:", res.stderr)
    else:
        print(f"[+] 100% Royalty-Free AI Demo Master created at {MP3_PATH} (320 kbps CBR)")

    # Cleanup temp WAV
    if WAV_PATH.exists():
        WAV_PATH.unlink()

if __name__ == "__main__":
    make_song_cover()
