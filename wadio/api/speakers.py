from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
from wadio.database import get_db
from wadio.models import User, Speaker

router = APIRouter(prefix="/speakers", tags=["speakers"])

DEFAULT_USER_ID = 1

def get_current_user(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(id=DEFAULT_USER_ID, email="default@local", role="admin", is_approved=True, is_active=True)
    return user

@router.get("/")
def list_speakers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    speakers = db.query(Speaker).filter(Speaker.user_id == current_user.id).all()
    return [{
        "id": s.id,
        "name": s.name,
        "speaker_id": s.speaker_id,
        "model_path": s.model_path,
        "is_default": s.is_default,
        "created_at": s.created_at.isoformat()
    } for s in speakers]

@router.delete("/{speaker_id}")
def delete_speaker(
    speaker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id, Speaker.user_id == current_user.id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    if speaker.model_path and shutil.os.path.exists(speaker.model_path):
        shutil.rmtree(speaker.model_path)
    
    db.delete(speaker)
    db.commit()
    return {"status": "deleted"}

@router.post("/{speaker_id}/set-default")
def set_default_speaker(
    speaker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id, Speaker.user_id == current_user.id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    db.query(Speaker).filter(Speaker.user_id == current_user.id).update({"is_default": False})
    speaker.is_default = True
    db.commit()
    
    return {"status": "updated", "is_default": True}
