from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import aiofiles
import os
import soundfile as sf
from wadio.database import get_db
from wadio.models import User, VoiceFile
from wadio.config import VOICE_DIR

router = APIRouter(prefix="/voice-files", tags=["voice-files"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import JWTError
    from wadio.config import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/upload")
async def upload_voice_file(
    file: UploadFile = File(...),
    transcript: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV files allowed")
    
    user_dir = VOICE_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_dir / file.filename
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    try:
        info = sf.info(str(file_path))
        duration = info.duration
    except:
        duration = 0.0
    
    voice_file = VoiceFile(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        transcript=transcript,
        duration=duration
    )
    db.add(voice_file)
    db.commit()
    db.refresh(voice_file)
    
    return {"id": voice_file.id, "filename": voice_file.filename, "duration": duration}

@router.get("/")
def list_voice_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    files = db.query(VoiceFile).filter(VoiceFile.user_id == current_user.id).all()
    return [{"id": f.id, "filename": f.filename, "duration": f.duration, "transcript": f.transcript} for f in files]

@router.delete("/{file_id}")
def delete_voice_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.query(VoiceFile).filter(VoiceFile.id == file_id, VoiceFile.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    db.delete(file)
    db.commit()
    return {"status": "deleted"}
