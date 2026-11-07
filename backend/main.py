import os
import sys
import shutil
import tempfile
from pathlib import Path

# Ensure backend directory is in sys.path regardless of execution working directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Patch torchaudio for soundfile decoding across all endpoints
import soundfile as sf
import torch
import torchaudio

def _soundfile_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, format=None, buffer_size=None, backend=None):
    data, sr = sf.read(str(uri), start=frame_offset, stop=None, dtype='float32')
    if num_frames > 0:
        data = data[:num_frames]
    tensor = torch.from_numpy(data)
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 2 and channels_first:
        tensor = tensor.t()
    return tensor, sr

torchaudio.load = _soundfile_load

from models_manager import (
    get_all_models_status,
    download_model,
    delete_model,
    get_system_metrics,
    get_all_generations,
    is_f5_installed,
    is_stable_audio_installed,
    is_stable_audio_3_installed,
    is_llama_installed,
    is_xtts_installed,
    is_fish_installed,
    is_audioldm_installed,
    MODELS_DIR,
    OUTPUTS_DIR
)
from tts_engine import tts_engine
from sfx_engine import sfx_engine
from llama_engine import llama_engine
from whisper_engine import whisper_engine
from audio_cleaner import clean_audio
from text_preprocessor import (
    preprocess_for_f5tts,
    preprocess_for_xtts,
    preprocess_for_fish,
    preprocess_text_for_engine,
    extract_tags,
    should_route_to_fish
)

try:
    from xtts_engine import xtts_engine
    XTTS_AVAILABLE = True
except Exception as _xtts_err:
    xtts_engine = None
    XTTS_AVAILABLE = False
    print(f"[Main] XTTS-v2 engine not available: {_xtts_err}")

try:
    from fish_engine import fish_engine
    FISH_AVAILABLE = True
except Exception as _fish_err:
    fish_engine = None
    FISH_AVAILABLE = False
    print(f"[Main] Fish Speech engine not available: {_fish_err}")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
VOICES_DIR = BASE_DIR / "backend" / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Preset voice catalog — matches files in backend/voices/
PRESET_VOICES = [
    {"id": "daan",    "name": "Daan 🇳🇱",   "description": "Nederlands (Man) · Helder & Krachtig",   "gender": "male",    "ref_text": "Hallo, mijn naam is Daan. Ik spreek vloeiend Nederlands met een heldere en natuurlijke stem.", "file": "daan_nl.wav"},
    {"id": "femke",   "name": "Femke 🇳🇱",  "description": "Nederlands (Vrouw) · Warm & Vriendelijk","gender": "female",  "ref_text": "Hoi, ik ben Femke. Welkom bij de Nederlandse stem presets voor XonAudio Studio.", "file": "femke_nl.wav"},
    {"id": "bram",    "name": "Bram 🇳🇱",   "description": "Nederlands (Man) · Diep & Rustgevend",   "gender": "male",    "ref_text": "Goedendag. Mijn naam is Bram. Ik ben een rustige en betrouwbare Nederlandse stem voor al jouw verhalen.", "file": "bram_nl.wav"},
    {"id": "lotte",   "name": "Lotte 🇳🇱",  "description": "Nederlands (Vrouw) · Expressief & Fris", "gender": "female",  "ref_text": "Hoi allemaal! Ik ben Lotte. Laten we samen geweldige en expressieve Nederlandse audio maken.", "file": "lotte_nl.wav"},
    {"id": "aria",    "name": "Aria 🇬🇧",   "description": "Female · Warm & Natural",        "gender": "female",  "ref_text": "", "file": "aria.wav"},
    {"id": "nova",    "name": "Nova 🇬🇧",   "description": "Female · Expressive Story Voice", "gender": "female",  "ref_text": "",  "file": "nova.flac"},
    {"id": "echo",    "name": "Echo 🇬🇧",   "description": "Male · Deep Country Voice",       "gender": "male",    "ref_text": "",  "file": "echo.flac"},
    {"id": "sage",    "name": "Sage 🇬🇧",   "description": "Male · Town Narrator",            "gender": "male",    "ref_text": "",  "file": "sage.flac"},
    {"id": "atlas",   "name": "Atlas 🇬🇧",  "description": "Neutral · Professional",          "gender": "neutral", "ref_text": "Some call me nature, others call me mother nature.", "file": "atlas.wav"},
    {"id": "default", "name": "Default",  "description": "Built-in F5-TTS reference voice", "gender": "neutral", "ref_text": "Some call me nature, others call me mother nature.", "file": "default.wav"},
]

app = FastAPI(
    title="XonAudio Studio API",
    description="F5-TTS Voice Cloning, Stable Audio Open Foley & Llama 3 Studio AI",
    version="1.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure outputs directory exists and mount static route
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
VOICES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Request Models
class DeleteModelRequest(BaseModel):
    model_key: str  # "f5_tts", "stable_audio", "llama", or "all"

class HFTokenRequest(BaseModel):
    token: str

class SFXGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "low quality, harsh, distorted, speech"
    duration: Optional[float] = 10.0
    steps: Optional[int] = 50
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    engine: Optional[str] = "stable_audio"  # "stable_audio" | "audioldm2"

class LlamaEnhanceRequest(BaseModel):
    prompt: str
    mode: Optional[str] = "sfx"  # "sfx" or "voice"

class LlamaChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class PreprocessTextRequest(BaseModel):
    text: str
    engine: Optional[str] = "f5_tts"

# ----------------- SYSTEM & MODELS ENDPOINTS -----------------

@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "XonAudio Studio is running smoothly"}

@app.get("/api/system/status")
def system_status():
    return get_system_metrics()

@app.get("/api/models/status")
def models_status():
    return get_all_models_status()

@app.post("/api/models/download/{model_key}")
def api_download_model(model_key: str):
    try:
        res = download_model(model_key)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/delete")
def api_delete_model(req: DeleteModelRequest):
    try:
        # Unload from GPU first
        if req.model_key in ("f5_tts", "all"):
            tts_engine.unload()
        if req.model_key in ("stable_audio", "all"):
            sfx_engine.unload()
        if req.model_key in ("stable_audio_3", "all"):
            sfx_engine.unload_stable_audio_3()
        if req.model_key in ("audioldm2", "all"):
            sfx_engine.unload_audioldm()
        if req.model_key in ("llama", "all"):
            llama_engine.unload()
        if req.model_key in ("xtts", "all") and XTTS_AVAILABLE and xtts_engine:
            xtts_engine.unload()
        if req.model_key in ("fish_speech", "all") and FISH_AVAILABLE and fish_engine:
            fish_engine.unload()

        res = delete_model(req.model_key)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/unload")
def api_unload_models():
    """Unloads all neural models from GPU VRAM."""
    try:
        tts_engine.unload()
        sfx_engine.unload()
        sfx_engine.unload_stable_audio_3()
        sfx_engine.unload_audioldm()
        llama_engine.unload()
        if XTTS_AVAILABLE and xtts_engine:
            xtts_engine.unload()
        if FISH_AVAILABLE and fish_engine:
            fish_engine.unload()
        whisper_engine.unload()
        return {"status": "success", "message": "All models unloaded from GPU memory."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/hf_token")
def save_hf_token(req: HFTokenRequest):
    """Saves the Hugging Face token to .env file for Stable Audio download."""
    token = req.token.strip()
    env_file = BASE_DIR / ".env"
    lines = []
    if env_file.exists():
        existing = env_file.read_text(encoding="utf-8").splitlines()
        lines = [l for l in existing if not l.startswith("HF_TOKEN=")]
    lines.append(f"HF_TOKEN={token}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Also set in current process environment
    os.environ["HF_TOKEN"] = token
    return {"status": "success", "message": "HF Token saved. You can now download Stable Audio Open."}

# ----------------- LLAMA AI ASSISTANT & MAGIC WAND -----------------

@app.post("/api/llama/enhance")
def enhance_prompt(req: LlamaEnhanceRequest):
    if not is_llama_installed():
        raise HTTPException(
            status_code=400,
            detail="Llama 3 model is not installed. Please download Llama 3 in the Model Manager tab or run Start_AudioStudio.bat."
        )
    try:
        enhanced = llama_engine.enhance_prompt(req.prompt, req.mode)
        return {"status": "success", "original": req.prompt, "enhanced": enhanced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llama/chat")
def llama_chat(req: LlamaChatRequest):
    if not is_llama_installed():
        raise HTTPException(
            status_code=400,
            detail="Llama 3 model is not installed. Please download Llama 3 in the Model Manager tab or run Start_AudioStudio.bat."
        )
    try:
        reply = llama_engine.chat(req.message, req.history)
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- GENERATIONS & PREVIOUS AUDIO -----------------

@app.get("/api/generations")
def list_generations():
    """Returns persistent list of previous audio generations."""
    try:
        return get_all_generations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/generations/{file_id}")
def delete_generation(file_id: str):
    """Deletes an audio file from outputs."""
    try:
        deleted = False
        for folder in ["tts", "sfx"]:
            target = OUTPUTS_DIR / folder / f"{file_id}.wav"
            if target.exists():
                target.unlink()
                deleted = True
                break
        if not deleted:
            raise HTTPException(status_code=404, detail="Audio file not found")
        return {"status": "success", "message": "Audio file removed from library"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- VOICE LIBRARY ENDPOINTS -----------------

@app.get("/api/voices")
def list_voices():
    """Returns the preset voice catalog plus any user-uploaded custom voices."""
    voices = []
    for v in PRESET_VOICES:
        voice_file = v.get("file", f"{v['id']}.wav")
        wav = VOICES_DIR / voice_file
        # Try fallback extensions
        if not wav.exists():
            for ext in [".wav", ".flac", ".mp3"]:
                candidate = VOICES_DIR / f"{v['id']}{ext}"
                if candidate.exists():
                    wav = candidate
                    break
        voices.append({
            **{k: val for k, val in v.items() if k != "file"},
            "type": "preset",
            "audio_url": f"/api/voices/{v['id']}/audio" if wav.exists() else None,
            "available": wav.exists(),
        })
    # Scan for user-uploaded custom voices
    custom_dir = VOICES_DIR / "custom"
    if custom_dir.exists():
        for f in sorted(custom_dir.glob("*.*")):
            if f.suffix.lower() in [".wav", ".flac", ".mp3", ".m4a"]:
                voices.append({
                    "id": f"custom_{f.stem}",
                    "name": f.stem.replace("_", " ").title(),
                    "description": "Custom · Uploaded by you",
                    "gender": "custom",
                    "ref_text": "",
                    "type": "custom",
                    "audio_url": f"/api/voices/custom/{f.name}/audio",
                    "available": True,
                })
    return voices

@app.get("/api/voices/{voice_id}/audio")
def get_preset_voice_audio(voice_id: str):
    """Streams a preset voice audio file for in-browser preview."""
    # Find the voice definition
    voice_def = next((v for v in PRESET_VOICES if v["id"] == voice_id), None)
    if voice_def:
        voice_file = voice_def.get("file", f"{voice_id}.wav")
        wav = VOICES_DIR / voice_file
        if wav.exists():
            media_type = "audio/flac" if wav.suffix == ".flac" else "audio/wav"
            return FileResponse(str(wav), media_type=media_type)
    # Fallback: try extensions
    for ext in [".wav", ".flac", ".mp3"]:
        wav = VOICES_DIR / f"{voice_id}{ext}"
        if wav.exists():
            media_type = "audio/flac" if ext == ".flac" else "audio/wav"
            return FileResponse(str(wav), media_type=media_type)
    raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' audio not found")

@app.get("/api/voices/custom/{filename}/audio")
def get_custom_voice_audio(filename: str):
    """Streams a user-uploaded custom voice WAV."""
    wav = VOICES_DIR / "custom" / filename
    if not wav.exists():
        raise HTTPException(status_code=404, detail="Custom voice audio not found")
    ext = wav.suffix.lower()
    media_type_map = {".wav": "audio/wav", ".flac": "audio/flac", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}
    return FileResponse(str(wav), media_type=media_type_map.get(ext, "audio/wav"))

@app.post("/api/voices/upload")
async def upload_custom_voice(
    voice_file: UploadFile = File(...),
    voice_name: Optional[str] = Form(""),
):
    """Saves a user-uploaded voice reference audio as a reusable custom voice."""
    custom_dir = VOICES_DIR / "custom"
    custom_dir.mkdir(parents=True, exist_ok=True)

    if not voice_file.content_type or not voice_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Please upload a valid audio file (WAV, MP3, FLAC).")

    stem = voice_name.strip().replace(" ", "_") if voice_name and voice_name.strip() else Path(voice_file.filename).stem
    # Sanitize
    stem = "".join(c for c in stem if c.isalnum() or c in "_-")[:40] or "custom_voice"
    suffix = Path(voice_file.filename).suffix or ".wav"
    out_path = custom_dir / f"{stem}{suffix}"

    with open(str(out_path), "wb") as f:
        shutil.copyfileobj(voice_file.file, f)

    # Automatically clean uploaded custom voice (VAD silence trim + -20 LUFS)
    try:
        clean_audio(str(out_path), str(out_path))
    except Exception as _c_err:
        print(f"[Main] Warning cleaning custom voice audio: {_c_err}")

    return {
        "status": "success",
        "voice_id": f"custom_{stem}",
        "name": stem.replace("_", " ").title(),
        "audio_url": f"/api/voices/custom/{stem}{suffix}/audio",
        "message": f"Custom voice '{stem}' saved successfully."
    }

@app.delete("/api/voices/custom/{filename}")
def delete_custom_voice(filename: str):
    """Deletes a user-uploaded custom voice."""
    wav = VOICES_DIR / "custom" / filename
    if not wav.exists():
        raise HTTPException(status_code=404, detail="Custom voice not found")
    wav.unlink()
    return {"status": "success", "message": f"Custom voice '{filename}' deleted."}

# ----------------- AUDIO GENERATION ENDPOINTS -----------------

def _resolve_voice_path(voice_id: str) -> Optional[str]:
    """Resolve a voice_id to a file path on disk (preset or custom)."""
    if not voice_id:
        return None
    if voice_id.startswith("custom_"):
        stem = voice_id[len("custom_"):]
        for ext in [".wav", ".flac", ".mp3", ".m4a"]:
            candidate = VOICES_DIR / "custom" / f"{stem}{ext}"
            if candidate.exists():
                return str(candidate)
        for f in (VOICES_DIR / "custom").glob(f"{stem}.*"):
            return str(f)
    else:
        voice_def = next((v for v in PRESET_VOICES if v["id"] == voice_id), None)
        if voice_def:
            vf = VOICES_DIR / voice_def.get("file", f"{voice_id}.wav")
            if vf.exists():
                return str(vf)
            for ext in [".wav", ".flac"]:
                c = VOICES_DIR / f"{voice_id}{ext}"
                if c.exists():
                    return str(c)
    return None


def _cleanup_temp(path: Optional[str]):
    """Remove a temp file if it was written to the temp directory."""
    import tempfile as _tf
    if path and path.startswith(_tf.gettempdir()) and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

@app.post("/api/transcribe")
def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form("auto"),
    clean: Optional[bool] = Form(True),
):
    """
    Transcribes reference audio using local Faster-Whisper (CUDA)
    and optionally cleans/normalizes the audio (-20 LUFS & silence trim).
    """
    temp_path = None
    cleaned_path = None
    try:
        suffix = Path(audio_file.filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            if hasattr(audio_file.file, "seek"):
                audio_file.file.seek(0)
            shutil.copyfileobj(audio_file.file, tmp)
            temp_path = tmp.name

        clean_flag = str(clean).lower() in ("true", "1", "yes")
        audio_for_whisper = temp_path
        if clean_flag:
            cleaned_path = clean_audio(temp_path)
            audio_for_whisper = cleaned_path

        result = whisper_engine.transcribe(audio_for_whisper, language=language)
        return {
            "status": "success",
            "transcript": result.get("text", ""),
            "language": result.get("language", ""),
            "language_probability": result.get("language_probability", 0.0),
            "duration": result.get("duration", 0.0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        _cleanup_temp(temp_path)
        _cleanup_temp(cleaned_path)

@app.post("/api/preprocess-text")
def api_preprocess_text(req: PreprocessTextRequest):
    """Parses emotion tags and cleans text according to target engine."""
    cleaned, tags = preprocess_text_for_engine(req.text, req.engine)
    route_fish = should_route_to_fish(req.text)
    return {
        "status": "success",
        "original": req.text,
        "cleaned": cleaned,
        "tags": tags,
        "should_route_to_fish": route_fish,
    }

@app.post("/api/tts/generate")
async def generate_tts(
    gen_text: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(""),
    ref_text: Optional[str] = Form(""),
    speed: Optional[float] = Form(1.0),
    nfe_steps: Optional[int] = Form(32),
    remove_silence: Optional[bool] = Form(True),
    language: Optional[str] = Form("en"),
    emotion: Optional[str] = Form(""),
):
    if not is_f5_installed():
        raise HTTPException(
            status_code=400,
            detail="F5-TTS model checkpoint is missing. Download it in Model Manager or restart via Start_AudioStudio.bat."
        )
    temp_ref_path = None
    cleaned_ref_path = None
    resolved_ref_text = ref_text or ""

    # Clean spoken text: strip brackets, convert [laugh] to Haha!, remove stage directions
    effective_gen_text = preprocess_for_f5tts(gen_text)

    try:
        if ref_audio and ref_audio.filename:
            # User uploaded a file directly in this request
            suffix = Path(ref_audio.filename).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(ref_audio.file, tmp)
                temp_ref_path = tmp.name
        elif voice_id:
            # Resolve preset or custom voice from library
            if voice_id.startswith("custom_"):
                filename = voice_id[len("custom_"):]
                for ext in [".wav", ".flac", ".mp3", ".m4a"]:
                    candidate = VOICES_DIR / "custom" / f"{filename}{ext}"
                    if candidate.exists():
                        temp_ref_path = str(candidate)
                        break
                if not temp_ref_path:
                    for f in (VOICES_DIR / "custom").glob(f"{filename}.*"):
                        temp_ref_path = str(f)
                        break
            else:
                voice_def = next((v for v in PRESET_VOICES if v["id"] == voice_id), None)
                if voice_def:
                    voice_file = voice_def.get("file", f"{voice_id}.wav")
                    preset_path = VOICES_DIR / voice_file
                    if not preset_path.exists():
                        for ext in [".wav", ".flac"]:
                            c = VOICES_DIR / f"{voice_id}{ext}"
                            if c.exists():
                                preset_path = c
                                break
                    if preset_path.exists():
                        temp_ref_path = str(preset_path)
                        if not resolved_ref_text:
                            resolved_ref_text = voice_def.get("ref_text", "")

        # Clean reference audio: VAD silence trim + -20 LUFS volume normalization + clamp to 10s
        active_ref_path = temp_ref_path
        if temp_ref_path and os.path.exists(temp_ref_path):
            try:
                cleaned_ref_path = clean_audio(temp_ref_path, max_duration_sec=10.0)
                active_ref_path = cleaned_ref_path
            except Exception as _c_err:
                print(f"[TTS] Warning cleaning reference audio: {_c_err}")
                active_ref_path = temp_ref_path

        # If reference text is missing, automatically transcribe with Whisper to prevent hallucinations/stuttering
        if active_ref_path and os.path.exists(active_ref_path) and not resolved_ref_text.strip():
            try:
                print("[TTS] Auto-transcribing reference audio with local Faster-Whisper...")
                w_res = whisper_engine.transcribe(active_ref_path, language=language)
                resolved_ref_text = w_res.get("text", "")
                print(f"[TTS] Auto-transcribed reference text: '{resolved_ref_text}'")
            except Exception as _w_err:
                print(f"[TTS] Faster-Whisper auto-transcription warning: {_w_err}")

        audio_url = tts_engine.generate(
            gen_text=effective_gen_text,
            ref_audio_path=active_ref_path,
            ref_text=resolved_ref_text,
            speed=float(speed),
            nfe_steps=int(nfe_steps),
            remove_silence=bool(remove_silence)
        )

        return {
            "status": "success",
            "audio_url": audio_url,
            "text": effective_gen_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup_temp(temp_ref_path)
        _cleanup_temp(cleaned_ref_path)

@app.post("/api/xtts/generate")
async def generate_xtts(
    gen_text: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(""),
    language: Optional[str] = Form("en"),
    speed: Optional[float] = Form(1.0),
    emotion: Optional[str] = Form(""),
):
    """Generate speech using XTTS-v2 — 17 languages including Dutch."""
    if not XTTS_AVAILABLE or xtts_engine is None:
        raise HTTPException(status_code=503, detail="XTTS-v2 engine unavailable. Install TTS library: pip install TTS")
    if not is_xtts_installed():
        raise HTTPException(status_code=400, detail="XTTS-v2 model not installed. Download it in Model Manager.")
    temp_ref_path = None
    cleaned_ref_path = None
    # Strip brackets so XTTS never reads them aloud
    clean_gen_text = preprocess_for_xtts(gen_text)
    try:
        if ref_audio and ref_audio.filename:
            suffix = Path(ref_audio.filename).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(ref_audio.file, tmp)
                temp_ref_path = tmp.name
        elif voice_id:
            temp_ref_path = _resolve_voice_path(voice_id)

        active_ref_path = temp_ref_path
        if temp_ref_path and os.path.exists(temp_ref_path):
            try:
                cleaned_ref_path = clean_audio(temp_ref_path, max_duration_sec=10.0)
                active_ref_path = cleaned_ref_path
            except Exception as _c_err:
                print(f"[XTTS] Warning cleaning reference audio: {_c_err}")
                active_ref_path = temp_ref_path

        audio_url = xtts_engine.generate(
            gen_text=clean_gen_text,
            ref_audio_path=active_ref_path,
            language=language or "en",
            speed=float(speed),
            emotion=emotion or "",
        )
        return {"status": "success", "audio_url": audio_url, "text": clean_gen_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup_temp(temp_ref_path)
        _cleanup_temp(cleaned_ref_path)


@app.post("/api/fish/generate")
async def generate_fish(
    gen_text: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(""),
    ref_text: Optional[str] = Form(""),
    language: Optional[str] = Form("en"),
    speed: Optional[float] = Form(1.0),
    emotion: Optional[str] = Form(""),
):
    """Generate speech using Fish Speech 1.5 — fully local, native emotion tags."""
    if not FISH_AVAILABLE or fish_engine is None:
        raise HTTPException(status_code=503, detail="Fish Speech engine unavailable. Check backend installation.")
    if not is_fish_installed():
        raise HTTPException(status_code=400, detail="Fish Speech 1.5 not installed. Download it in Model Manager.")
    temp_ref_path = None
    cleaned_ref_path = None
    # Preprocess text for Fish Speech (normalizes tags [laughs] -> [laugh], removes unsupported brackets)
    clean_gen_text = preprocess_for_fish(gen_text)
    resolved_ref_text = ref_text or ""
    try:
        if ref_audio and ref_audio.filename:
            suffix = Path(ref_audio.filename).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(ref_audio.file, tmp)
                temp_ref_path = tmp.name
        elif voice_id:
            temp_ref_path = _resolve_voice_path(voice_id)

        active_ref_path = temp_ref_path
        if temp_ref_path and os.path.exists(temp_ref_path):
            try:
                cleaned_ref_path = clean_audio(temp_ref_path, max_duration_sec=10.0)
                active_ref_path = cleaned_ref_path
            except Exception as _c_err:
                print(f"[Fish] Warning cleaning reference audio: {_c_err}")
                active_ref_path = temp_ref_path

        # If ref text missing, auto-transcribe with Whisper
        if active_ref_path and os.path.exists(active_ref_path) and not resolved_ref_text.strip():
            try:
                w_res = whisper_engine.transcribe(active_ref_path, language=language)
                resolved_ref_text = w_res.get("text", "")
            except Exception as _w_err:
                print(f"[Fish] Whisper transcription warning: {_w_err}")

        audio_url = fish_engine.generate(
            gen_text=clean_gen_text,
            ref_audio_path=active_ref_path,
            ref_text=resolved_ref_text,
            language=language or "en",
            speed=float(speed),
            emotion=emotion or "",
        )
        return {"status": "success", "audio_url": audio_url, "text": clean_gen_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup_temp(temp_ref_path)
        _cleanup_temp(cleaned_ref_path)


@app.get("/api/xtts/languages")
def get_xtts_languages():
    from xtts_engine import SUPPORTED_LANGUAGES as XTTS_LANGS
    return [{"code": k, "name": v} for k, v in XTTS_LANGS.items()]


@app.get("/api/fish/languages")
def get_fish_languages():
    from fish_engine import SUPPORTED_LANGUAGES as FISH_LANGS
    return [{"code": k, "name": v} for k, v in FISH_LANGS.items()]


@app.post("/api/sfx/generate")
def generate_sfx(req: SFXGenerateRequest):
    engine_choice = getattr(req, "engine", "stable_audio") or "stable_audio"
    if engine_choice == "audioldm2":
        if not is_audioldm_installed():
            raise HTTPException(
                status_code=400,
                detail="AudioLDM 2 model checkpoint is missing. Download it in Model Manager or restart via Start_AudioStudio.bat."
            )
        try:
            audio_url = sfx_engine.generate_audioldm(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                duration=req.duration or 10.0,
                steps=req.steps or 40,
                guidance_scale=req.cfg_scale or 4.0,
                seed=req.seed if req.seed is not None else -1
            )
            return {
                "status": "success",
                "audio_url": audio_url,
                "prompt": req.prompt,
                "duration": req.duration,
                "engine": "audioldm2"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif engine_choice == "stable_audio_3":
        if not is_stable_audio_3_installed():
            raise HTTPException(
                status_code=400,
                detail="Stable Audio 3 Medium model checkpoint is missing. Download it in Model Manager or restart via Start_AudioStudio.bat."
            )
        try:
            audio_url = sfx_engine.generate_stable_audio_3(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                duration=req.duration or 10.0,
                steps=req.steps or 8,
                cfg_scale=req.cfg_scale or 7.0,
                seed=req.seed if req.seed is not None else -1
            )
            return {
                "status": "success",
                "audio_url": audio_url,
                "prompt": req.prompt,
                "duration": req.duration,
                "engine": "stable_audio_3"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        if not is_stable_audio_installed():
            raise HTTPException(
                status_code=400,
                detail="Stable Audio Open model checkpoint is missing. Download it in Model Manager or restart via Start_AudioStudio.bat."
            )
        try:
            audio_url = sfx_engine.generate(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                duration=req.duration,
                steps=req.steps,
                cfg_scale=req.cfg_scale,
                seed=req.seed
            )
            return {
                "status": "success",
                "audio_url": audio_url,
                "prompt": req.prompt,
                "duration": req.duration,
                "engine": "stable_audio"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ----------------- SERVE BUILT FRONTEND IF PRESENT -----------------

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    print("[XonAudio Studio] Starting FastAPI server on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
