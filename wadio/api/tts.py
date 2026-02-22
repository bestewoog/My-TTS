from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from jose import jwt
import torch
import soundfile as sf
import uuid
from pathlib import Path
from wadio.database import get_db
from wadio.models import User, Speaker
from wadio.config import OUTPUT_DIR, QWEN_MODEL_PATH, QWEN_DEVICE

router = APIRouter(prefix="/tts", tags=["tts"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_model_cache = {}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from wadio.config import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_model(model_path: Optional[str] = None):
    model_key = model_path or "default"
    if model_key not in _model_cache:
        from qwen_tts import Qwen3TTSModel
        load_path = model_path if model_path else QWEN_MODEL_PATH
        _model_cache[model_key] = Qwen3TTSModel.from_pretrained(
            load_path,
            device_map=QWEN_DEVICE,
            dtype=torch.bfloat16,
        )
    return _model_cache[model_key]

def get_latest_checkpoint(checkpoint_dir: Path) -> Optional[str]:
    if not checkpoint_dir.exists():
        return None
    
    checkpoints = [d for d in checkpoint_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-epoch-")]
    if not checkpoints:
        return None
    
    checkpoints.sort(key=lambda x: int(x.name.split("-")[-1]))
    return str(checkpoints[-1])

class SynthesizeRequest(BaseModel):
    text: str
    speaker: str
    language: str = "auto"
    instruction: Optional[str] = None

@router.post("/synthesize")
def synthesize(
    request: SynthesizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    speaker = db.query(Speaker).filter(
        Speaker.name == request.speaker,
        Speaker.user_id == current_user.id
    ).first()
    
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    model_path = None
    if speaker.model_path:
        checkpoint_dir = Path(speaker.model_path)
        latest_checkpoint = get_latest_checkpoint(checkpoint_dir)
        if latest_checkpoint:
            model_path = latest_checkpoint
    
    model = get_model(model_path)
    
    wavs, sr = model.generate_custom_voice(
        text=request.text,
        speaker=request.speaker,
        language=request.language,
        instruct=request.instruction
    )
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_filename = f"{uuid.uuid4()}.wav"
    output_path = OUTPUT_DIR / output_filename
    sf.write(str(output_path), wavs[0], sr)
    
    return {
        "audio_filename": output_filename,
        "message": "Audio generated successfully"
    }

@router.get("/audio/{filename}")
def get_audio(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    audio_path = OUTPUT_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    return FileResponse(
        str(audio_path),
        media_type="audio/wav",
        filename=filename
    )

@router.get("/default-speakers")
def get_default_speakers():
    model = get_model()
    speakers = model.get_supported_speakers()
    return {"speakers": speakers}
