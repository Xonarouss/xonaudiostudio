"""
Song Cover Engine for XonAudio Studio
Handles the complete 4-stage song cover transformation pipeline:
  [1/4 Audio Ophalen]            -> URL download via yt-dlp or direct file upload
  [2/4 Vocals Scheiden]          -> State-of-the-art BS-RoFormer (audio-separator on CUDA)
  [3/4 Stem Converteren]         -> RVC v2 voice conversion with neural RMVPE pitch extraction & HuBERT
  [4/4 Afmixen]                  -> Dynamic volume mixing, phase alignment & soft-knee peak protection
"""

import os
import gc
import sys
import json
import time
import uuid
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable

import numpy as np
import soundfile as sf
import torch
import torch.nn.functional as F

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
RVC_MODELS_DIR = MODELS_DIR / "rvc"
BS_ROFORMER_DIR = MODELS_DIR / "bs_roformer"
OUTPUTS_DIR = BASE_DIR / "outputs" / "song_covers"
INPUTS_DIR = OUTPUTS_DIR / "inputs"
STEMS_DIR = OUTPUTS_DIR / "stems"
MIXES_DIR = OUTPUTS_DIR / "mixes"

# Ensure all workspace directories exist
for p in [RVC_MODELS_DIR, BS_ROFORMER_DIR, OUTPUTS_DIR, INPUTS_DIR, STEMS_DIR, MIXES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Add RVC source path for infer_pack & rmvpe
RVC_SRC_DIR = BASE_DIR / "backend" / "rvc_src"
if RVC_SRC_DIR.exists() and str(RVC_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(RVC_SRC_DIR))

logger = logging.getLogger("SongCoverEngine")
logger.setLevel(logging.INFO)


class SongCoverEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_half = (self.device == "cuda")
        self.rmvpe = None
        self.hubert = None
        self.separator = None

    def list_installed_rvc_models(self) -> List[Dict[str, Any]]:
        """
        Scans models/rvc for all user voice models (.pth files).
        Excludes system weight files (rmvpe.pt, hubert_base.pt).
        """
        models = []
        if not RVC_MODELS_DIR.exists():
            return models

        # Excluded checkpoints
        system_weights = {"rmvpe.pt", "hubert_base.pt", "hubert.pt"}

        for pth in RVC_MODELS_DIR.glob("**/*.pth"):
            if pth.name.lower() in system_weights:
                continue

            # Model ID / display name
            model_id = pth.stem
            model_name = pth.stem.replace("_", " ").title()

            # Check if matching .index file exists in same or adjacent dir
            index_candidates = list(pth.parent.glob(f"*{pth.stem}*.index")) + list(pth.parent.glob("*.index"))
            index_path = str(index_candidates[0]) if index_candidates else None

            # Read basic metadata from checkpoint if readable
            version = "v2"
            sr = 40000
            try:
                cpt = torch.load(pth, map_location="cpu", weights_only=False)
                version = cpt.get("version", "v2")
                if "config" in cpt and len(cpt["config"]) > 0:
                    sr = cpt["config"][-1]
                del cpt
            except Exception:
                pass

            models.append({
                "id": pth.name,
                "name": model_name,
                "filename": pth.name,
                "path": str(pth),
                "has_index": index_path is not None,
                "index_path": index_path,
                "version": version,
                "sample_rate": sr,
                "size_mb": round(pth.stat().st_size / (1024 * 1024), 1)
            })

        return sorted(models, key=lambda m: m["name"])

    def fetch_url_audio(self, url: str) -> Path:
        """
        Downloads YouTube or other supported web audio using yt-dlp.
        Returns the path to the downloaded pristine audio file.
        """
        import yt_dlp

        unique_id = uuid.uuid4().hex[:10]
        out_template = str(INPUTS_DIR / f"input_{unique_id}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        # If Spotify link: search track on YouTube
        if "spotify.com" in url:
            ydl_opts["default_search"] = "ytsearch"

        logger.info(f"Downloading audio from {url}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        expected_wav = INPUTS_DIR / f"input_{unique_id}.wav"
        if expected_wav.exists():
            return expected_wav

        # In case extension differed
        candidates = list(INPUTS_DIR.glob(f"input_{unique_id}.*"))
        if candidates:
            return candidates[0]

        raise RuntimeError(f"Audio download failed for URL: {url}")

    def separate_vocals_bs_roformer(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Tuple[Path, Path]:
        """
        Separates audio into (vocals_path, instrumental_path) using BS-RoFormer
        via the audio-separator library with native CUDA acceleration.
        """
        from audio_separator.separator import Separator

        if progress_callback:
            progress_callback("BS-RoFormer laden op GPU...", 0.25)

        logger.info(f"[BS-RoFormer] Starting vocal separation for {audio_path.name}...")
        
        # Ensure other pipelines are unloaded to save VRAM
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        separator = Separator(
            model_file_dir=str(BS_ROFORMER_DIR),
            output_dir=str(STEMS_DIR),
            output_format="WAV",
        )

        model_name = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
        separator.load_model(model_filename=model_name)

        if progress_callback:
            progress_callback("Vocals en instrumentaal isoleren...", 0.50)

        output_files = separator.separate(str(audio_path))
        
        # Free separator from VRAM
        separator = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        vocals_path = None
        instrumental_path = None

        for fname in output_files:
            fpath = STEMS_DIR / fname
            lower = fname.lower()
            if "(vocals)" in lower or "vocals" in lower:
                vocals_path = fpath
            elif "(instrumental)" in lower or "instrumental" in lower or "other" in lower:
                instrumental_path = fpath

        if not vocals_path or not instrumental_path:
            raise RuntimeError(f"BS-RoFormer stem separation did not output expected stems: {output_files}")

        logger.info(f"[BS-RoFormer] Successfully separated:\n  Vocals: {vocals_path}\n  Instrumental: {instrumental_path}")
        return vocals_path, instrumental_path

    def load_rmvpe(self):
        """Loads RMVPE pitch extraction model."""
        if self.rmvpe is not None:
            return self.rmvpe

        from rmvpe import RMVPE
        rmvpe_path = RVC_MODELS_DIR / "rmvpe.pt"
        if not rmvpe_path.exists():
            raise FileNotFoundError(f"RMVPE weights not found at {rmvpe_path}. Download via Model Manager.")

        logger.info(f"Loading RMVPE from {rmvpe_path} on {self.device}...")
        self.rmvpe = RMVPE(str(rmvpe_path), is_half=self.is_half, device=self.device)
        return self.rmvpe

    def load_hubert(self):
        """Loads pure-PyTorch HuBERT Base model from torchaudio (no fairseq dependency)."""
        if self.hubert is not None:
            return self.hubert

        import torchaudio
        logger.info(f"Loading HuBERT Base from torchaudio on {self.device}...")
        bundle = torchaudio.pipelines.HUBERT_BASE
        model = bundle.get_model()
        model.eval().to(self.device)
        if self.is_half:
            model = model.half()
        self.hubert = model
        return self.hubert

    def convert_vocals_rvc(
        self,
        vocals_path: Path,
        model_filename: str,
        pitch_shift: int = 0,
        index_rate: float = 0.75,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Path:
        """
        Transforms isolated vocals using RVC v2 model with RMVPE pitch extraction.
        """
        from lib.infer_pack.models import (
            SynthesizerTrnMs256NSFsid,
            SynthesizerTrnMs256NSFsid_nono,
            SynthesizerTrnMs768NSFsid,
            SynthesizerTrnMs768NSFsid_nono
        )
        import faiss

        if progress_callback:
            progress_callback("RVC stemmodel en RMVPE initialiseren...", 0.60)

        pth_path = RVC_MODELS_DIR / model_filename
        if not pth_path.exists():
            # Search subdirectories of models/rvc
            matches = list(RVC_MODELS_DIR.glob(f"**/{model_filename}"))
            if matches:
                pth_path = matches[0]
            else:
                raise FileNotFoundError(f"RVC model checkpoint not found: {model_filename}")

        logger.info(f"[RVC] Loading voice checkpoint: {pth_path}...")
        cpt = torch.load(pth_path, map_location="cpu", weights_only=False)
        tgt_sr = cpt["config"][-1]
        cpt["config"][-3] = cpt["weight"]["emb_g.weight"].shape[0]  # n_spk
        if_f0 = cpt.get("f0", 1)
        version = cpt.get("version", "v2")

        if version == "v1":
            if if_f0 == 1:
                net_g = SynthesizerTrnMs256NSFsid(*cpt["config"], is_half=self.is_half)
            else:
                net_g = SynthesizerTrnMs256NSFsid_nono(*cpt["config"])
        elif version == "v2":
            if if_f0 == 1:
                net_g = SynthesizerTrnMs768NSFsid(*cpt["config"], is_half=self.is_half)
            else:
                net_g = SynthesizerTrnMs768NSFsid_nono(*cpt["config"])
        else:
            raise ValueError(f"Unknown RVC version in checkpoint: {version}")

        del net_g.enc_q
        net_g.load_state_dict(cpt["weight"], strict=False)
        net_g.eval().to(self.device)
        if self.is_half:
            net_g = net_g.half()
        else:
            net_g = net_g.float()

        # Check for FAISS index file
        index_candidates = list(pth_path.parent.glob(f"*{pth_path.stem}*.index")) + list(pth_path.parent.glob("*.index"))
        index = None
        big_npy = None
        if index_candidates and index_rate > 0:
            try:
                index_file = str(index_candidates[0])
                logger.info(f"[RVC] Loading feature index: {index_file}...")
                index = faiss.read_index(index_file)
                big_npy = index.reconstruct_n(0, index.ntotal)
            except Exception as idx_err:
                logger.warning(f"[RVC] Could not load FAISS index: {idx_err}. Proceeding without index retrieval.")
                index = None
                big_npy = None

        if progress_callback:
            progress_callback("Toonhoogte (RMVPE F0) en HuBERT features berekenen...", 0.75)

        # 1. Read input vocals & resample to 16kHz for HuBERT and RMVPE
        audio_np, in_sr = sf.read(str(vocals_path))
        if audio_np.ndim > 1:
            audio_np = np.mean(audio_np, axis=1)

        import librosa
        if in_sr != 16000:
            audio_16k = librosa.resample(audio_np, orig_sr=in_sr, target_sr=16000)
        else:
            audio_16k = audio_np.copy()

        # 2. Extract Pitch using RMVPE
        rmvpe_model = self.load_rmvpe()
        f0 = rmvpe_model.infer_from_audio(audio_16k, thred=0.03)

        # Apply pitch shift in semitones (-12 to +12)
        if pitch_shift != 0:
            f0 *= pow(2, float(pitch_shift) / 12.0)

        # Quantize coarse pitch to mel scale bins 1..255
        f0_min = 50.0
        f0_max = 1100.0
        f0_mel_min = 1127.0 * np.log(1.0 + f0_min / 700.0)
        f0_mel_max = 1127.0 * np.log(1.0 + f0_max / 700.0)

        f0_mel = 1127.0 * np.log(1.0 + np.maximum(f0, 0.0) / 700.0)
        f0_mel[f0_mel > 0] = (f0_mel[f0_mel > 0] - f0_mel_min) * 254.0 / (f0_mel_max - f0_mel_min) + 1.0
        f0_mel[f0_mel <= 1] = 1.0
        f0_mel[f0_mel > 255] = 255.0
        f0_coarse = np.rint(f0_mel).astype(np.int64)

        pitch = torch.as_tensor(f0_coarse, device=self.device, dtype=torch.long).unsqueeze(0)
        pitchf = torch.as_tensor(f0, device=self.device, dtype=torch.float32).unsqueeze(0)
        if self.is_half:
            pitchf = pitchf.half()

        # 3. Extract HuBERT features
        hubert_model = self.load_hubert()
        audio_tensor = torch.as_tensor(audio_16k, device=self.device, dtype=torch.float32).unsqueeze(0)
        if self.is_half:
            audio_tensor = audio_tensor.half()

        with torch.no_grad():
            extracted_layers, _ = hubert_model.extract_features(audio_tensor)
            # Layer 12 for v2, Layer 9 for v1
            layer_idx = 11 if version == "v2" else 8
            feats = extracted_layers[min(layer_idx, len(extracted_layers) - 1)]

        # 4. Optional Index Retrieval
        if index is not None and big_npy is not None and index_rate > 0:
            npy = feats[0].cpu().float().numpy()
            score, ix = index.search(npy, k=8)
            weight = np.square(1.0 / np.maximum(score, 1e-6))
            weight /= weight.sum(axis=1, keepdims=True)
            retrieved_npy = np.sum(big_npy[ix] * np.expand_dims(weight, axis=2), axis=1)

            retrieved_tensor = torch.as_tensor(retrieved_npy, device=self.device, dtype=feats.dtype).unsqueeze(0)
            feats = retrieved_tensor * index_rate + (1.0 - index_rate) * feats

        # 5. Interpolate features to frame length (x2 scale)
        feats = F.interpolate(feats.permute(0, 2, 1), scale_factor=2).permute(0, 2, 1)

        p_len = min(feats.shape[1], pitch.shape[1])
        feats = feats[:, :p_len]
        pitch = pitch[:, :p_len]
        pitchf = pitchf[:, :p_len]
        p_len_t = torch.tensor([p_len], device=self.device, dtype=torch.long)
        sid = torch.tensor([0], device=self.device, dtype=torch.long)

        if progress_callback:
            progress_callback("Stem transformeren (VITS/HiFi-GAN synthese)...", 0.85)

        # 6. Generator Synthesis
        with torch.no_grad():
            if if_f0 == 1:
                out_audio = net_g.infer(feats, p_len_t, pitch, pitchf, sid)[0][0, 0]
            else:
                out_audio = net_g.infer(feats, p_len_t, sid)[0][0, 0]

            out_audio_np = out_audio.detach().cpu().float().numpy()

        # Free generator from VRAM
        del net_g, cpt, feats, pitch, pitchf
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        unique_id = uuid.uuid4().hex[:8]
        converted_path = STEMS_DIR / f"vocals_converted_{unique_id}.wav"
        sf.write(str(converted_path), out_audio_np, tgt_sr)
        logger.info(f"[RVC] Voice converted successfully: {converted_path}")
        return converted_path

    def mix_stems(
        self,
        converted_vocals_path: Path,
        instrumental_path: Path,
        vocal_vol: float = 1.0,
        inst_vol: float = 1.0,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, str]:
        """
        Mixes converted vocals and instrumental tracks according to volume sliders.
        Applies soft-knee peak protection to avoid digital clipping.
        Generates Full Mix, Vocals Only, and Instrumental Only.
        """
        if progress_callback:
            progress_callback("Volledige cover en stems afmixen...", 0.92)

        voc_audio, voc_sr = sf.read(str(converted_vocals_path))
        inst_audio, inst_sr = sf.read(str(instrumental_path))

        # Ensure stereo for both
        if voc_audio.ndim == 1:
            voc_audio = np.stack([voc_audio, voc_audio], axis=-1)
        if inst_audio.ndim == 1:
            inst_audio = np.stack([inst_audio, inst_audio], axis=-1)

        # Resample vocals to instrumental sample rate if different
        import librosa
        if voc_sr != inst_sr:
            voc_l = librosa.resample(voc_audio[:, 0], orig_sr=voc_sr, target_sr=inst_sr)
            voc_r = librosa.resample(voc_audio[:, 1], orig_sr=voc_sr, target_sr=inst_sr)
            voc_audio = np.stack([voc_l, voc_r], axis=-1)
            voc_sr = inst_sr

        # Align length to longest track
        max_len = max(len(voc_audio), len(inst_audio))
        if len(voc_audio) < max_len:
            pad = np.zeros((max_len - len(voc_audio), 2), dtype=voc_audio.dtype)
            voc_audio = np.concatenate([voc_audio, pad], axis=0)
        elif len(inst_audio) < max_len:
            pad = np.zeros((max_len - len(inst_audio), 2), dtype=inst_audio.dtype)
            inst_audio = np.concatenate([inst_audio, pad], axis=0)

        # Apply volume multipliers
        v_mult = max(0.0, min(1.5, float(vocal_vol)))
        i_mult = max(0.0, min(1.5, float(inst_vol)))

        voc_scaled = voc_audio * v_mult
        inst_scaled = inst_audio * i_mult

        # Mix with soft-knee peak limiting
        mixed = voc_scaled + inst_scaled
        peak = np.max(np.abs(mixed))
        if peak > 0.95:
            # Soft-knee compression to preserve acoustic dynamics without harsh clipping
            mixed = np.tanh(mixed / peak) * 0.95

        unique_id = uuid.uuid4().hex[:8]
        mix_filename = f"cover_mix_{unique_id}.wav"
        voc_filename = f"cover_vocals_{unique_id}.wav"
        inst_filename = f"cover_inst_{unique_id}.wav"

        mix_path = MIXES_DIR / mix_filename
        voc_path = MIXES_DIR / voc_filename
        inst_path = MIXES_DIR / inst_filename

        sf.write(str(mix_path), mixed, inst_sr)
        sf.write(str(voc_path), voc_scaled, inst_sr)
        sf.write(str(inst_path), inst_scaled, inst_sr)

        logger.info(f"Mix export complete:\n  Mix: {mix_path}\n  Vocals: {voc_path}\n  Inst: {inst_path}")

        return {
            "mix_url": f"/outputs/song_covers/mixes/{mix_filename}",
            "vocals_url": f"/outputs/song_covers/mixes/{voc_filename}",
            "instrumental_url": f"/outputs/song_covers/mixes/{inst_filename}",
            "mix_path": str(mix_path),
            "vocals_path": str(voc_path),
            "instrumental_path": str(inst_path),
        }

    def process_song_cover(
        self,
        source_type: str,
        file_path_or_url: str,
        model_name: str,
        pitch_shift: int = 0,
        index_rate: float = 0.75,
        vocal_vol: float = 1.0,
        inst_vol: float = 1.0,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the 4-step Song Cover pipeline end-to-end.
        """
        t0 = time.time()

        # Step 1: Audio ophalen
        if progress_callback:
            progress_callback("Audio ophalen en voorbereiden...", 0.10)

        if source_type == "url":
            input_audio_path = self.fetch_url_audio(file_path_or_url)
        else:
            input_audio_path = Path(file_path_or_url)
            if not input_audio_path.exists():
                raise FileNotFoundError(f"Uploaded input audio file not found: {file_path_or_url}")

        # Step 2: Vocals scheiden (BS-RoFormer)
        if progress_callback:
            progress_callback("Vocals en instrumental isoleren met BS-RoFormer...", 0.30)
        vocals_path, inst_path = self.separate_vocals_bs_roformer(input_audio_path, progress_callback)

        # Step 3: Stem converteren (RVC v2 RMVPE)
        if progress_callback:
            progress_callback("Stem converteren via RVC v2 en RMVPE...", 0.65)
        converted_vocals_path = self.convert_vocals_rvc(
            vocals_path=vocals_path,
            model_filename=model_name,
            pitch_shift=pitch_shift,
            index_rate=index_rate,
            progress_callback=progress_callback
        )

        # Step 4: Afmixen
        if progress_callback:
            progress_callback("Afmixen van vocals en instrumental...", 0.90)
        mix_results = self.mix_stems(
            converted_vocals_path=converted_vocals_path,
            instrumental_path=inst_path,
            vocal_vol=vocal_vol,
            inst_vol=inst_vol,
            progress_callback=progress_callback
        )

        elapsed = round(time.time() - t0, 1)
        if progress_callback:
            progress_callback("Klaar!", 1.0)

        return {
            "status": "success",
            "elapsed_seconds": elapsed,
            "mix_url": mix_results["mix_url"],
            "vocals_url": mix_results["vocals_url"],
            "instrumental_url": mix_results["instrumental_url"],
        }


song_cover_engine = SongCoverEngine()

