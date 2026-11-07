# 🎙️ AI Audio Studio - F5-TTS & Stable Audio Open

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![CUDA 12.4+](https://img.shields.io/badge/CUDA-12.4%2B-76B900.svg)](https://developer.nvidia.com/cuda-zone)
[![Built by Xonarous Inc](https://img.shields.io/badge/Built_by-Xonarous_Inc-06B6D4.svg)](https://xonarous.nl)

**An ultra-modern, local all-in-one AI Audio Studio for zero-shot Voice Cloning (F5-TTS) and high-fidelity Sound Effects / Foley diffusion (Stable Audio Open).**

[Features](#-features) • [Quickstart](#-quickstart) • [Model Management](#-model-management) • [Architecture](#-architecture) • [License](#-license)

</div>

---

## 🌟 Why AI Audio Studio?

Most state-of-the-art open-source audio models are scattered across complex Python scripts, requiring manual checkpoint handling, clunky web UIs, and deep terminal knowledge.

**AI Audio Studio** bridges this gap:
- **1-Click Launch on Windows:** No command line wrestling — just double-click `Start_AudioStudio.bat`.
- **Integrated Model Manager:** Download weights on-demand or wipe them in 1 click directly from the UI to reclaim tens of gigabytes of disk space.
- **Hardware Acceleration:** Native PyTorch CUDA acceleration with GDDR7 VRAM monitoring for modern GPUs (RTX 40/50-series).
- **Pro Studio Experience:** Glassmorphism dark interface, interactive waveform scrubbing, speed/pitch controls, and instant `.wav` downloads.

---

## ✨ Features

### 1. 🗣️ Voice Lab (F5-TTS v1)
- **Zero-Shot Voice Cloning:** Clone any voice with just 5–10 seconds of clean reference audio.
- **Multilingual TTS:** Fluid, natural speech flow matching human rhythm and inflection.
- **Customization:** Fine-tune speech rate, NFE sampling steps (16–64), and toggle silence removal.
- **Interactive Waveform:** Scrub, inspect, replay, and download 24kHz/48kHz studio-quality WAV files.

### 2. 🎛️ Sound Studio (Stable Audio Open 1.0)
- **Cinematic Foley & SFX:** Generate hyper-realistic explosions, footsteps, sci-fi weapons, ambient drones, and weather.
- **Duration Control:** Full slider control from **1 second up to 47 seconds** at 44.1kHz stereo.
- **Advanced Diffusion:** Adjust CFG guidance scale, inference steps (25–100), and custom/random seeds.
- **Curated Presets:** Instant prompt presets for immediate inspiration.

### 3. 💾 Storage & Model Manager
- **Status Dashboard:** Shows real-time disk consumption per model (e.g., F5-TTS: ~2.3 GB, Stable Audio Open: ~4.8 GB).
- **Reclaim Disk Space:** Delete individual models or click *[Verwijder Alles]* to completely free your drive.
- **VRAM Monitor:** Real-time GPU memory monitoring and a 1-click *[Maak VRAM Vrij]* button.

---

## 🚀 Quickstart

### Prerequisites
- **OS:** Windows 10/11 or Linux (Ubuntu 22.04+)
- **GPU:** NVIDIA GPU with 8GB+ VRAM (Recommended: 12GB–16GB, e.g., RTX 4070 / 4080 / 5080)
- **RAM:** 16 GB or higher (64 GB ideal)
- **Software:** [Python 3.10 or 3.11](https://www.python.org/) & [Node.js 18+](https://nodejs.org/)

---

### Windows (1-Click)
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ai-audio-studio.git
   cd ai-audio-studio
   ```
2. Double-click **`Start_AudioStudio.bat`**.
   - It automatically creates the virtual environment, configures PyTorch with CUDA, verifies model weights, and opens your browser at `http://localhost:5173`.

---

### Linux / WSL2
1. Clone and navigate to the directory:
   ```bash
   git clone https://github.com/your-username/ai-audio-studio.git
   cd ai-audio-studio
   ```
2. Make the start script executable and run:
   ```bash
   chmod +x start_audiostudio.sh
   ./start_audiostudio.sh
   ```

---

## 🏗️ Architecture

```
ai-audio-studio/
├── backend/
│   ├── main.py               # FastAPI backend with REST endpoints & static mounting
│   ├── models_manager.py     # Checkpoint verification, disk metrics & HuggingFace downloads
│   ├── tts_engine.py         # F5-TTS inference & voice conditioning engine
│   ├── sfx_engine.py         # Stable Audio Open stereo diffusion pipeline
│   ├── download_models.py    # Pre-launch model checker & downloader
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceLab.jsx      # Voice cloning UI
│   │   │   ├── SoundStudio.jsx   # Sound effects UI
│   │   │   ├── ModelManager.jsx  # Disk & VRAM management
│   │   │   ├── AudioPlayer.jsx   # Waveform visualizer & player
│   │   │   └── Footer.jsx        # Branding & specs bar
│   │   ├── App.jsx               # Main container & tab router
│   │   └── index.css             # Tailwind glassmorphism styles
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── models/                       # Dedicated directory for AI checkpoints
│   ├── f5-tts/
│   └── stable-audio-open/
├── outputs/                      # Generated .wav audio files
│   ├── tts/
│   └── sfx/
├── Start_AudioStudio.bat         # Windows automated launcher
├── start_audiostudio.sh          # Linux / WSL2 automated launcher
├── LICENSE                       # MIT License
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Healthcheck endpoint |
| `GET` | `/api/models/status` | List installed models, paths, and size in GB |
| `POST` | `/api/models/download/{model_key}` | Download missing model (`f5_tts` or `stable_audio`) |
| `POST` | `/api/models/delete` | Delete weights from disk to free storage space |
| `POST` | `/api/models/unload` | Unload models from GPU VRAM |
| `GET` | `/api/system/status` | GPU VRAM, System RAM, and Disk space stats |
| `POST` | `/api/tts/generate` | Generate voice cloning speech with F5-TTS |
| `POST` | `/api/sfx/generate` | Generate up to 47s stereo sound effects |

---

## 🤝 Model Attributions & Credits

- **F5-TTS:** Created by Yushen Chen et al. ([SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)).
- **Stable Audio Open:** Released by Stability AI ([stabilityai/stable-audio-open-1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0)).
- Built with **FastAPI**, **React**, **Vite**, **Tailwind CSS**, and **Lucide Icons**.

---

## 📄 License & Branding

Distributed under the **MIT License**. See `LICENSE` for more information.

Built with ❤️ by [**Xonarous Inc**](https://xonarous.nl).
