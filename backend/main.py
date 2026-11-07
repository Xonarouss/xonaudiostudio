import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models_manager import (
    get_all_models_status,
    download_model,
    delete_model,
    get_system_metrics,
    MODELS_DIR
)
from tts_engine import tts_engine
from sfx_engine import sfx_engine

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(
    title="AI Audio Studio API",
    description="F5-TTS Voice Cloning & Stable Audio Open SFX Backend",
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
    model_key: str  # "f5_tts", "stable_audio", or "all"

class SFXGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "low quality, harsh, distorted, speech"
    duration: Optional[float] = 10.0
    steps: Optional[int] = 50
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1

# ----------------- SYSTEM & MODELS ENDPOINTS -----------------

@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "AI Audio Studio is running smoothly"}

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

        res = delete_model(req.model_key)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/unload")
def api_unload_models():
    """Unloads all loaded AI models from GPU VRAM."""
    try:
        tts_engine.unload()
        sfx_engine.unload()
        return {"status": "success", "message": "Alle modellen zijn ontladen uit het GPU VRAM geheugen."}
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
    print("[AI Audio Studio] Starting FastAPI server on http://127.0.0.1:8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

