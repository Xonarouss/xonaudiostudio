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

# ----------------- AUDIO GENERATION ENDPOINTS -----------------

@app.post("/api/tts/generate")
async def generate_tts(
    gen_text: str = Form(...),
    ref_audio: Optional[UploadFile] = File(None),
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
    try:
        if ref_audio:
            suffix = Path(ref_audio.filename).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(ref_audio.file, tmp)
                temp_ref_path = tmp.name

        audio_url = tts_engine.generate(
            gen_text=gen_text,
            ref_audio_path=temp_ref_path,
            ref_text=ref_text or "",
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
        if temp_ref_path and os.path.exists(temp_ref_path):
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
