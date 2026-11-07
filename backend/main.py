import os
import shutil
import tempfile
from pathlib import Path
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
    is_llama_installed,
    MODELS_DIR,
    OUTPUTS_DIR
)
from tts_engine import tts_engine
from sfx_engine import sfx_engine
from llama_engine import llama_engine

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
VOICES_DIR = BASE_DIR / "backend" / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Preset voice catalog — matches files in backend/voices/
PRESET_VOICES = [
    {"id": "aria",    "name": "Aria",  "description": "Female · Warm & Clear",          "gender": "female",  "ref_text": "Some call me nature, others call me mother nature."},
    {"id": "nova",    "name": "Nova",  "description": "Female · Bright & Expressive",   "gender": "female",  "ref_text": "Some call me nature, others call me mother nature."},
    {"id": "echo",    "name": "Echo",  "description": "Male · Deep & Authoritative",    "gender": "male",    "ref_text": "Some call me nature, others call me mother nature."},
    {"id": "atlas",   "name": "Atlas", "description": "Male · Natural & Casual",        "gender": "male",    "ref_text": "Some call me nature, others call me mother nature."},
    {"id": "sage",    "name": "Sage",  "description": "Neutral · Calm & Professional",  "gender": "neutral", "ref_text": "Some call me nature, others call me mother nature."},
    {"id": "default", "name": "Default (Basic)", "description": "Built-in reference voice", "gender": "neutral", "ref_text": "Some call me nature, others call me mother nature."},
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

class SFXGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "low quality, harsh, distorted, speech"
    duration: Optional[float] = 10.0
    steps: Optional[int] = 50
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1

class LlamaEnhanceRequest(BaseModel):
    prompt: str
    mode: Optional[str] = "sfx"  # "sfx" or "voice"

class LlamaChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

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
        if req.model_key in ("llama", "all"):
            llama_engine.unload()

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
        llama_engine.unload()
        return {"status": "success", "message": "All models unloaded from GPU memory."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        wav = VOICES_DIR / f"{v['id']}.wav"
        voices.append({
            **v,
            "type": "preset",
            "audio_url": f"/api/voices/{v['id']}/audio" if wav.exists() else None,
            "available": wav.exists(),
        })
    # Scan for user-uploaded custom voices
    custom_dir = VOICES_DIR / "custom"
    if custom_dir.exists():
        for f in sorted(custom_dir.glob("*.wav")):
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
    """Streams a preset voice WAV for in-browser preview."""
    wav = VOICES_DIR / f"{voice_id}.wav"
    if not wav.exists():
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' audio not found")
    return FileResponse(str(wav), media_type="audio/wav")

@app.get("/api/voices/custom/{filename}/audio")
def get_custom_voice_audio(filename: str):
    """Streams a user-uploaded custom voice WAV."""
    wav = VOICES_DIR / "custom" / filename
    if not wav.exists():
        raise HTTPException(status_code=404, detail="Custom voice audio not found")
    return FileResponse(str(wav), media_type="audio/wav")

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

@app.post("/api/tts/generate")
async def generate_tts(
    gen_text: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(""),
    ref_text: Optional[str] = Form(""),
    speed: Optional[float] = Form(1.0),
    nfe_steps: Optional[int] = Form(32),
    remove_silence: Optional[bool] = Form(True)
):
    if not is_f5_installed():
        raise HTTPException(
            status_code=400,
            detail="F5-TTS model checkpoint is missing. Download it in Model Manager or restart via Start_AudioStudio.bat."
        )
    temp_ref_path = None
    resolved_ref_text = ref_text or ""

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
                # Try with .wav extension
                candidate = VOICES_DIR / "custom" / f"{filename}.wav"
                if not candidate.exists():
                    # Try without extension transform
                    for f in (VOICES_DIR / "custom").glob(f"{filename}.*"):
                        candidate = f
                        break
                if candidate.exists():
                    temp_ref_path = str(candidate)
            else:
                preset_wav = VOICES_DIR / f"{voice_id}.wav"
                if preset_wav.exists():
                    temp_ref_path = str(preset_wav)
                    # Look up the ref_text for this preset
                    for pv in PRESET_VOICES:
                        if pv["id"] == voice_id:
                            if not resolved_ref_text:
                                resolved_ref_text = pv["ref_text"]
                            break

        audio_url = tts_engine.generate(
            gen_text=gen_text,
            ref_audio_path=temp_ref_path,
            ref_text=resolved_ref_text,
            speed=float(speed),
            nfe_steps=int(nfe_steps),
            remove_silence=bool(remove_silence)
        )

        return {
            "status": "success",
            "audio_url": audio_url,
            "text": gen_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Only remove if it was a true temp file (not a library voice)
        if temp_ref_path and temp_ref_path.startswith(tempfile.gettempdir()) and os.path.exists(temp_ref_path):
            try:
                os.remove(temp_ref_path)
            except OSError:
                pass

@app.post("/api/sfx/generate")
def generate_sfx(req: SFXGenerateRequest):
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
            "duration": req.duration
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
