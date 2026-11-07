<div align="center">

# 🎙️ XONAUDIO STUDIO v1.2
### Next-Gen Local AI Audio Workstation • 3 Voice Engines (Dutch Support) • Foley & SFX Diffusion
**Built & Maintained by [Xonarous Inc](https://xonarous.nl)**

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20x64-blue.svg?style=for-the-badge&logo=windows)](https://xonarous.nl)
[![CUDA](https://img.shields.io/badge/CUDA-12.8%2B%20%7C%20PyTorch%202.12-green.svg?style=for-the-badge&logo=nvidia)](https://xonarous.nl)
[![Architecture](https://img.shields.io/badge/Architecture-Blackwell%20sm__120%20%7C%20Ada%20%7C%20Ampere-purple.svg?style=for-the-badge)](https://xonarous.nl)
[![Dutch](https://img.shields.io/badge/🇳🇱%20Dutch%20TTS-Supported%20(XTTS%20+%20Fish)-orange.svg?style=for-the-badge)](https://xonarous.nl)
[![Engines](https://img.shields.io/badge/Voice%20Engines-F5--TTS%20%7C%20XTTS--v2%20%7C%20Fish%20Speech-teal.svg?style=for-the-badge)](https://xonarous.nl)
[![Website](https://img.shields.io/badge/Live_Site-GitHub%20Pages-0ea5e9.svg?style=for-the-badge&logo=githubpages&logoColor=white)](https://xonarouss.github.io/xonaudiostudio/)
[![Buy me a beer](https://img.shields.io/badge/🍺%20Buy%20me%20a%20beer-buymeacoffee.com%2Fxonarous-amber.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/xonarous)
[![License](https://img.shields.io/badge/License-MIT%20Open%20Source-emerald.svg?style=for-the-badge)](https://github.com/Xonarouss/xonaudiostudio/blob/main/LICENSE)

[**🌐 Live Website**](https://xonarouss.github.io/xonaudiostudio/) • [**🍺 Buy Me a Beer**](https://buymeacoffee.com/xonarous) • [**Releases (.zip)**](https://github.com/Xonarouss/xonaudiostudio/releases) • [**Repository (GitHub)**](https://github.com/Xonarouss/xonaudiostudio) • [**Company (xonarous.nl)**](https://xonarous.nl)

</div>

---

## 🌟 Overview

**XonAudio Studio** is a turn-key, professional desktop workstation engineered for **100% on-device AI voice cloning, multilingual speech synthesis, and cinematic sound effects / foley generation**.

Unlike cloud-dependent platforms with monthly subscriptions, privacy concerns, and latency delays, XonAudio Studio runs completely on your local NVIDIA GPU with **zero cloud dependencies and zero remote API calls**. 

Switch effortlessly between **three neural voice synthesis engines**:
1. **F5-TTS v1 Base:** Flow-matching zero-shot voice cloning with fast ODE solver (English & Chinese Mandarin).
2. **Coqui XTTS-v2:** High-fidelity multilingual voice cloning across 17 languages, including native **Dutch (Nederlands 🇳🇱)**, German, French, Spanish, Italian, and more.
3. **Fish Speech 1.5 Ultra:** The newest dual autoregressive (DAR) + VQ-GAN neural audio codec architecture. Extremely fast, natural prosody, virtually artifact-free, with **Dutch (🇳🇱)** support.

Also includes **Stable Audio Open 1.0** for 44.1kHz stereo Foley diffusion up to 47 seconds, and **Meta Llama 3** for Magic Wand prompt expansion and creative studio direction.

Featuring a clean, ultra-modern **White Mode desktop interface** with live real-time hardware telemetry (GPU %, Temp, GDDR7 VRAM, Power Draw, RAM, CPU).

---

## ✨ Key Features

- **🔒 100% Local & Private:** Zero cloud telemetry, zero remote audio uploads. Your voice recordings, scripts, and generated WAV files stay strictly on your local PC.
- **⚡ Blackwell sm_120 Native Acceleration:** Powered by PyTorch CUDA 12.8 with native support for RTX 5080, 5090, 4080, and 4090 GPUs, plus automatic safe CPU fallback.
- **🗣️ 3-Engine Voice Lab Switcher:** 
  - **F5-TTS:** Fast non-autoregressive diffusion.
  - **XTTS-v2:** 17 Languages natively supported including 🇳🇱 **Dutch**.
  - **Fish Speech 1.5:** SOTA DAR + VQ-GAN vocoder, ultra-high quality, 🇳🇱 **Dutch** supported.
- **🇳🇱 Native Dutch Language Support:** Full high-fidelity Dutch speech synthesis and voice cloning via XTTS-v2 and Fish Speech 1.5.
- **🎛️ Sound Studio (Stable Audio Open):** 44.1kHz stereo audio diffusion up to 47 seconds per clip. Full control over duration, CFG guidance scale, inference steps (25–100), and custom/random seeds.
- **🪄 Llama 3 Magic Wand & AI Assistant:** Local Meta Llama 3 expands simple ideas into Hollywood acoustic directions, writes voice acting scripts with punctuation cues, and answers studio production questions.
- **📊 Real-Time Dynamic Hardware Monitor:** Live floating monitor widget displaying GPU Utilization, Temperature (°C), GDDR7 VRAM Consumption, System RAM, and CPU %.
- **📈 Live Neural Progress Bars:** Visual percentage bars (0% ➔ 100%), elapsed time, and stage indicators during audio synthesis.
- **💾 Automated Model Manager & Clean Storage:** Monitor local model sizes in GB, download weights on-demand, or purge checkpoints in 1 click to instantly reclaim tens of gigabytes.
- **🔄 Auto-Update Checking:** Automatically checks the official GitHub repo and Hugging Face commit hashes on launch; if a newer model revision or release exists, it updates automatically.
- **🖥️ Desktop Shortcut Generator:** Prompts on initial launch to create a branded `XonAudio Studio.lnk` on your Windows Desktop with the custom vector logo icon.

---

## 🧠 Neural Architecture & Foundation Models

XonAudio Studio coordinates 5 state-of-the-art open research foundation models (all 100% local):

| Model | Checkpoint Location | Size | Role | Precision / Output |
| :--- | :--- | :--- | :--- | :--- |
| **F5-TTS v1 Base** | `models/f5-tts/model_1250000.safetensors` | 2.3 GB | Zero-Shot Flow-Matching Speech (EN/ZH) | FP16 / 24kHz Vocos |
| **Coqui XTTS-v2** | `models/xtts-v2/` | 2.0 GB | Multilingual Voice Cloning (17 Langs incl. 🇳🇱 Dutch) | FP16 / 24kHz |
| **Fish Speech 1.5 Ultra** | `models/fish-speech-1.5/` | 0.7 GB | Dual-AR + VQ-GAN Neural Codec (incl. 🇳🇱 Dutch) | FP16 / 44.1kHz VQ-GAN |
| **Stable Audio Open 1.0** | `models/stable-audio-open/` | 4.8 GB | High-Resolution Stereo Foley & SFX Diffusion | FP16 / 44.1kHz Stereo |
| **Meta Llama 3 Studio AI** | `models/llama/` | 2.8 GB | Creative Prompt Engineering (Magic Wand 🪄) & Assistant | FP16 / Text Generation |

---

## 💻 Hardware Requirements & VRAM Profiles

XonAudio Studio automatically queries your hardware using native driver APIs and adapts precision dynamically:

```
+---------------------------------------------------------------------------------------+
|  Tier               | Target GPU                       | VRAM        | Mode           |
+---------------------+----------------------------------+-------------+----------------+
|  Minimum            | RTX 3060 12GB / RTX 4060 16GB    | 8 - 12 GB   | FP16 Sliced    |
|  Recommended Studio | RTX 4070Ti Super / RTX 4080 16GB | 16 GB       | Native FP16    |
|  Blackwell Flagship | RTX 5080 16GB / RTX 5090 32GB    | 16 - 32 GB  | sm_120 Native  |
+---------------------------------------------------------------------------------------+
```

- **System RAM:** 16 GB DDR4/DDR5 (32 GB – 64 GB recommended).
- **Storage:** 15 GB free NVMe SSD space for checkpoints and outputs.
- **OS:** Windows 10 / 11 64-bit or Linux (Ubuntu 22.04+ / WSL2).
- **NVIDIA Driver:** v570.xx or newer with CUDA 12.8 support.

---

## 🚀 Quickstart & Installation

### Option 1: Standalone Portable ZIP (Easiest)
1. Download **`XonAudio-Studio-v1.0.0-Portable.zip`** from [Releases](https://github.com/Xonarouss/xonaudiostudio/releases).
2. Extract the ZIP anywhere on your system.
3. Double-click **`Start_AudioStudio.bat`**.
   - The launcher configures your virtual environment, checks for model updates, offers to create a Desktop shortcut, and opens `http://localhost:5173` automatically.

---

### Option 2: Clone with Git
```bash
git clone https://github.com/Xonarouss/xonaudiostudio.git
cd xonaudiostudio
```
- **Windows:** Double-click **`Start_AudioStudio.bat`**
- **Linux / WSL2:** Run `./start_audiostudio.sh`

---

## 🛠️ REST API Reference

The backend provides a high-performance FastAPI server running on `http://127.0.0.1:8000`:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/system/status` | `GET` | Live dynamic metrics (GPU %, Temp, VRAM, Power, RAM, CPU) |
| `/api/models/status` | `GET` | List installed models, local paths, and size in GB |
| `/api/models/download/{key}` | `POST` | On-demand download of `f5_tts` or `stable_audio` |
| `/api/models/delete` | `POST` | Purge checkpoints to reclaim storage space |
| `/api/models/unload` | `POST` | Release models from GPU VRAM |
| `/api/tts/generate` | `POST` | F5-TTS zero-shot voice cloning endpoint |
| `/api/sfx/generate` | `POST` | Stable Audio Open sound effect diffusion endpoint |
| `/api/llama/enhance` | `POST` | Llama 3 Magic Wand prompt expansion endpoint |
| `/api/llama/chat` | `POST` | Llama 3 conversational audio engineering assistant |
| `/api/generations` | `GET` | Retrieve list of all previously generated audio clips |

---

## 🍺 Support & Community

If XonAudio Studio streamlines your audio workflow, support future model integrations with a beer!

<p align="center">
  <a href="https://buymeacoffee.com/xonarous" target="_blank">
    <img src="https://img.shields.io/badge/🍺%20Buy%20me%20a%20beer-buymeacoffee.com%2Fxonarous-amber.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white" alt="Buy Me A Beer" />
  </a>
  <a href="https://xonarous.nl" target="_blank">
    <img src="https://img.shields.io/badge/Official_Website-xonarous.nl-0891B2?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Xonarous Inc" />
  </a>
</p>

---

## ⚖️ License & Attribution

- **Publisher & Creator:** XonAudio Studio is built and maintained by **[Xonarous Inc](https://xonarous.nl)**.
- **License:** Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
- **F5-TTS:** Created by Yushen Chen et al. ([SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)).
- **Stable Audio Open:** Released by Stability AI ([stabilityai/stable-audio-open-1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0)).
- **Copyright:** © 2026 Xonarous Inc. All rights reserved.
