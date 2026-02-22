from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from jose import jwt
from wadio.database import get_db
from wadio.models import User, VoiceFile, FineTuneJob
from wadio.tasks.finetune import start_finetune_job

router = APIRouter(prefix="/finetune", tags=["finetune"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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

class FineTuneRequest(BaseModel):
    speaker_name: str
    voice_file_ids: List[int]
    epochs: int = 3
    batch_size: int = 2
    lr: float = 2e-5

@router.post("/start")
def start_finetune(
    request: FineTuneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    files = db.query(VoiceFile).filter(
        VoiceFile.id.in_(request.voice_file_ids),
        VoiceFile.user_id == current_user.id
    ).all()
    
    if len(files) != len(request.voice_file_ids):
        raise HTTPException(status_code=400, detail="Some voice files not found")
    
    job = FineTuneJob(
        user_id=current_user.id,
        speaker_name=request.speaker_name,
        config={"epochs": request.epochs, "batch_size": request.batch_size, "lr": request.lr},
        voice_file_ids=",".join(map(str, request.voice_file_ids)),
        status="queued"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    voice_file_data = [
        {"file_path": f.file_path, "transcript": f.transcript or ""}
        for f in files
    ]
    
    start_finetune_job(
        job.id,
        request.speaker_name,
        voice_file_data,
        {"epochs": request.epochs, "batch_size": request.batch_size, "lr": request.lr},
        db
    )
    
    return {"job_id": job.id, "status": "queued"}

@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = db.query(FineTuneJob).filter(FineTuneJob.user_id == current_user.id).all()
    return [{"id": j.id, "speaker_name": j.speaker_name, "status": j.status, "created_at": j.created_at.isoformat()} for j in jobs]

@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(FineTuneJob).filter(FineTuneJob.id == job_id, FineTuneJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "speaker_name": job.speaker_name,
        "status": job.status,
        "config": job.config,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

@router.delete("/jobs/{job_id}")
def cancel_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(FineTuneJob).filter(FineTuneJob.id == job_id, FineTuneJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in ["queued", "running"]:
        job.status = "cancelled"
        db.commit()
    
    return {"status": job.status}
