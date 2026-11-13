<div align="center">

# 🎙️ XONAUDIO STUDIO v1.3
### Next-Gen Local AI Audio Workstation • 3 Voice Engines (Dutch Support) • AI Song Cover Lab • 3 SFX Engines
**Built & Maintained by [Xonarous Inc](https://xonarous.nl)**

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20x64-blue.svg?style=for-the-badge&logo=windows)](https://xonarous.nl)
[![CUDA](https://img.shields.io/badge/CUDA-12.8%2B%20%7C%20PyTorch%202.12-green.svg?style=for-the-badge&logo=nvidia)](https://xonarous.nl)
[![Architecture](https://img.shields.io/badge/Architecture-Blackwell%20sm__120%20%7C%20Ada%20%7C%20Ampere-purple.svg?style=for-the-badge)](https://xonarous.nl)
[![Dutch](https://img.shields.io/badge/🇳🇱%20Dutch%20TTS-Supported%20(XTTS%20+%20Fish)-orange.svg?style=for-the-badge)](https://xonarous.nl)
[![Song Cover Lab](https://img.shields.io/badge/AI%20Song%20Cover-BS--RoFormer%20%2B%20RVC%20v2-pink.svg?style=for-the-badge)](https://xonarous.nl)
[![SFX Engines](https://img.shields.io/badge/SFX%20Diffusion-AudioLDM2%20%7C%20SA3%20Medium%20%7C%20SA%20Open-teal.svg?style=for-the-badge)](https://xonarous.nl)
[![Website](https://img.shields.io/badge/Live_Site-GitHub%20Pages-0ea5e9.svg?style=for-the-badge&logo=githubpages&logoColor=white)](https://xonarouss.github.io/xonaudiostudio/)
[![Buy me a beer](https://img.shields.io/badge/🍺%20Buy%20me%20a%20beer-buymeacoffee.com%2Fxonarous-amber.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/xonarous)
[![License](https://img.shields.io/badge/License-MIT%20Open%20Source-emerald.svg?style=for-the-badge)](https://github.com/Xonarouss/xonaudiostudio/blob/main/LICENSE)

[**🌐 Live Website**](https://xonarouss.github.io/xonaudiostudio/) • [**🍺 Buy Me a Beer**](https://buymeacoffee.com/xonarous) • [**Releases (.zip)**](https://github.com/Xonarouss/xonaudiostudio/releases) • [**Repository (GitHub)**](https://github.com/Xonarouss/xonaudiostudio) • [**Company (xonarous.nl)**](https://xonarous.nl)

</div>

---

## 🌟 Overview

**XonAudio Studio** is a turn-key, professional desktop workstation engineered for **100% on-device AI voice cloning, full AI song cover production, multilingual speech synthesis, and cinematic sound effects / Foley generation**.

Unlike cloud-dependent platforms with monthly subscriptions, privacy concerns, and latency delays, XonAudio Studio runs completely on your local NVIDIA GPU with **zero cloud dependencies and zero remote API calls**.

### 🎛️ Five Dedicated Studio Workspaces:
1. **[Voice Lab]**: Switch seamlessly between **3 neural speech synthesis engines**:
   - **F5-TTS v1 Base:** Flow-matching zero-shot voice cloning with fast ODE solver (English & Chinese Mandarin).
   - **Coqui XTTS-v2:** High-fidelity multilingual voice cloning across 17 languages, including native **Dutch (Nederlands 🇳🇱)**, German, French, Spanish, Italian, and more.
   - **Fish Speech 1.5 Ultra:** Dual autoregressive (DAR) + VQ-GAN neural audio codec architecture. Extremely fast, natural prosody, virtually artifact-free, with native **Dutch (🇳🇱)** support.
2. **[SFX Studio]**: Triple sound effect & Foley diffusion suite:
   - **Stable Audio Open 1.0:** 44.1kHz stereo Foley and musical clips up to 47 seconds.
   - **Stable Audio 3 Medium DiT:** Stability AI's cutting-edge Diffusion Transformer with 10-step high-speed synthesis and CFG guidance.
   - **AudioLDM 2 Studio:** Dual CLAP + T5 narrative sound effect synthesis designed for multi-event soundscapes.
   - **Intelligent Negative Prompt Sanitization:** Automatically detects vocal and musical intent (e.g., laughter, screams, crying, instruments) and cleans negative prompt conflicts dynamically.
3. **[Song Cover Lab]**: Complete end-to-end AI Song Cover production pipeline:
   - **Audio Ingestion:** Drag-and-drop song files (MP3/WAV/FLAC) or fetch directly from YouTube/Spotify links.
   - **Target Singer Flexibility:** Use pre-trained RVC models (`.pth`), upload an audio clip, or **extract voice samples directly from any YouTube URL** to clone singers on the fly.
   - **BS-RoFormer Vocal Isolation:** SOTA 12.97 SDR separation on CUDA to cleanly isolate singing vocals and instrumental stems with zero bleed.
   - **Studio De-Reverb Expander:** Built-in downward expander attenuates room reflections and slapback echo by 15–22 dB while keeping singing phonemes 100% intact.
   - **Silence-Aware Phrase Boundary Slicing:** Dynamically searches energy minima (±1.5s window) to ensure words are never cut across chunk boundaries.
   - **RVC v2 + RMVPE Neural Voice Conversion:** Transform vocals using any RVC v2 model or voice reference, with pitch-tracking RMVPE and pitch shifting (-12 to +12 semitones).
   - **Bit-Exact Pure-PyTorch Fairseq HuBERT:** Native 100% bit-exact acoustic encoder integration with unvoiced consonant protection.
   - **Dynamic Stem Mixing:** Independent volume sliders for vocals (0% - 150%) and instrumental (0% - 150%) with soft-knee peak protection.
   - **Dual Studio Quality Export:** Broadcast-ready **320 kbps High-Fidelity MP3** and **24-bit Lossless Studio Master WAV**.
4. **[Generations Archive]**: Integrated audio library cataloging all synthesized clips with waveform players, prompt metadata, and batch export tools. Automatically catalogs song covers with track titles and cover artist badges (`Midnight Echoes — Studio AI Cover`).
5. **[Model Manager]**: 1-click inspection, on-demand downloading, VRAM unloading, and checkpoint purging for all local models.

---

## ✨ Key Features

- **🔒 100% Local & Private:** Zero cloud telemetry, zero remote audio uploads. Your voice recordings, scripts, and generated audio files stay strictly on your local PC.
- **⚡ Blackwell sm_120 Native Acceleration:** Powered by PyTorch CUDA 12.8 with native support for RTX 5080, 5090, 4080, and 4090 GPUs, plus automatic safe CPU fallback.
- **🎵 Song Cover Lab Pipeline:** 4-stage pipeline `[1/4 Audio Acquisition] ➔ [2/4 BS-RoFormer Vocal Separation] ➔ [3/4 RVC v2 Voice Conversion] ➔ [4/4 Hi-Fi Mixing & Mastering]`.
- **🎤 Instant Voice Cloning for Covers:** Use pre-trained `.pth` models or clone any singing artist from audio on the fly by uploading a reference voice audio sample.
- **🗣️ 3-Engine Voice Lab:** F5-TTS, XTTS-v2, and Fish Speech 1.5 with full native **Dutch (🇳🇱)** support.
- **🇳🇱 Enhanced Dutch Preset Voices:** Studio-quality 24kHz PCM native Dutch presets (`daan_nl`, `femke_nl`, `bram_nl`, `lotte_nl`) and expressive laughter synthesis (`[laugh]`, `*laughs*`).
- **🎛️ Triple SFX Diffusion Suite:** Stable Audio Open 1.0, Stable Audio 3 Medium DiT, and AudioLDM 2 with negative prompt sanitization.
- **🪄 Llama 3 Magic Wand & AI Co-Pilot:** Local Meta Llama 3 expands simple ideas into Hollywood acoustic directions and provides interactive studio assistance.
- **📊 Real-Time Dynamic Hardware Monitor:** Live floating monitor widget displaying GPU %, Temperature (°C), GDDR7 VRAM, Power Draw (Watts), System RAM, and CPU %.
- **💎 Hi-Fi Dual Export Quality:** Every generation can be exported as both **320 kbps MP3** (FFmpeg libmp3lame) and **24-bit Lossless PCM WAV** (`PCM_24`).
- **👤 Studio Identity & Profile:** Configurable studio profile with **Nickname** (e.g. *Chris*), **Avatar** (preset SVG & custom image uploads), and **Naam van Herkomst / Origin** (e.g. *Kerkrade*), displayed across the header, AI Assistant chat, and generation archive.
- **💾 Automated Model Manager:** Inspect checkpoint sizes in GB, download missing models on-demand, or wipe unused models in 1 click.
- **🚀 Automated Startup Scripts:** `Start_AudioStudio.bat` automatically configures dependencies, checks for model updates, on-demand downloads missing checkpoints, and opens the app.

---

## 🧠 Neural Architecture & Foundation Models

XonAudio Studio coordinates 9 state-of-the-art open research foundation models (all 100% local):

| Model | Checkpoint Location | Size | Role | Precision / Output |
| :--- | :--- | :--- | :--- | :--- |
| **F5-TTS v1 Base** | `models/f5-tts/model_1250000.safetensors` | 2.3 GB | Zero-Shot Flow-Matching Speech (EN/ZH) | FP16 / 24kHz Vocos |
| **Coqui XTTS-v2** | `models/xtts-v2/` | 2.0 GB | Multilingual Voice Cloning (17 Langs incl. 🇳🇱 Dutch) | FP16 / 24kHz |
| **Fish Speech 1.5 Ultra** | `models/fish-speech-1.5/` | 0.7 GB | Dual-AR + VQ-GAN Neural Codec (incl. 🇳🇱 Dutch) | FP16 / 44.1kHz VQ-GAN |
| **BS-RoFormer Vocal Separator** | `models/bs_roformer/model_bs_roformer_ep_317_sdr_12.9755.ckpt` | 0.64 GB | SOTA 12.97 SDR Vocal & Instrumental Stem Separation | FP16 / 44.1kHz Stereo |
| **RVC v2 Neural Voice Converter** | `models/rvc/` | Variable | Singing & Speaking Voice Conversion with FAISS Index | FP16 / 48kHz / 40kHz |
| **RMVPE Pitch Extractor** | `models/rvc/rmvpe.pt` | 0.18 GB | Deep Neural Fundamental Frequency ($F_0$) Extraction | FP16 / 100 FPS |
| **Fairseq HuBERT Base** | `models/rvc/hubert_base.pt` | 0.19 GB | Acoustic Phonetic Representation (Bit-Exact pure-PyTorch) | FP16 / 768-dim Layer 12 |
| **Stable Audio Open 1.0** | `models/stable-audio-open/` | 4.8 GB | High-Resolution Stereo Foley & SFX Diffusion | FP16 / 44.1kHz Stereo |
| **Stable Audio 3 Medium** | `models/stable-audio-3-repo/` | 3.2 GB | DiT Diffusion Transformer Sound Design (10-Step) | FP16 / 44.1kHz Stereo |
| **AudioLDM 2 Studio** | `models/audioldm2-repo/` | 1.8 GB | Dual CLAP + T5 Multi-Event Narrative Foley | FP16 / 16kHz / 48kHz |
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
+---------------------+----------------------------------+-------------+----------------+
```

- **System RAM:** 16 GB DDR4/DDR5 (32 GB – 64 GB recommended).
- **Storage:** 20 GB free NVMe SSD space for checkpoints and stems.
- **OS:** Windows 10 / 11 64-bit or Linux (Ubuntu 22.04+ / WSL2).
- **NVIDIA Driver:** v570.xx or newer with CUDA 12.8 support.

---

## 🚀 Quickstart & Installation

### Option 1: Standalone Portable ZIP (Easiest)
1. Download **`XonAudio-Studio-v1.3.0-Portable.zip`** from [Releases](https://github.com/Xonarouss/xonaudiostudio/releases).
2. Extract the ZIP anywhere on your system.
3. Double-click **`Start_AudioStudio.bat`**.
   - The launcher configures your virtual environment, checks for model updates, downloads any missing checkpoints on-demand, and opens `http://localhost:5173` automatically.

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
| `/api/system/status` | `GET` | Live dynamic hardware metrics (GPU %, Temp, VRAM, Power, RAM, CPU) |
| `/api/models/status` | `GET` | List installed models, local paths, and size in GB |
| `/api/models/download/{key}` | `POST` | On-demand download of foundation models |
| `/api/models/delete` | `POST` | Purge checkpoints to reclaim storage space |
| `/api/models/unload` | `POST` | Release models from GPU VRAM |
| `/api/tts/generate` | `POST` | Voice Lab speech synthesis endpoint (F5-TTS, XTTS-v2, Fish Speech) |
| `/api/sfx/generate` | `POST` | SFX Studio diffusion endpoint (Stable Audio Open, SA3 Medium, AudioLDM 2) |
| `/api/song-cover/process` | `POST` | Full AI Song Cover 4-stage pipeline execution |
| `/api/song-cover/fetch-url` | `POST` | Download and convert YouTube or Spotify song audio |
| `/api/song-cover/models` | `GET` | Scan and list installed RVC voice models (.pth) |
| `/api/song-cover/upload-model` | `POST` | Upload and register custom RVC `.pth` and `.index` voice models |
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
- **BS-RoFormer:** Created by Ju-Chiang Wang et al. (ByteDance).
- **RVC v2 & RMVPE:** Retrieval-based Voice Conversion & RMVPE pitch extraction project.
- **F5-TTS:** Created by Yushen Chen et al. ([SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)).
- **Stable Audio:** Released by Stability AI ([stabilityai/stable-audio-open-1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0)).
- **Fish Speech:** Released by Fish Audio ([fishaudio/fish-speech](https://github.com/fishaudio/fish-speech)).
- **Copyright:** © 2026 Xonarous Inc. All rights reserved.
