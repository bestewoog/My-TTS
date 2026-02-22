from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from jose import jwt
from wadio.database import get_db
from wadio.models import User
from wadio.core.auth import verify_password, get_password_hash, create_access_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_approved: bool
    is_active: bool

    class Config:
        from_attributes = True

class ApprovalResponse(BaseModel):
    id: int
    email: str
    is_approved: bool
    created_at: str

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

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    from wadio.config import ADMIN_EMAIL
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    is_approved = user.email == ADMIN_EMAIL
    
    new_user = User(
        email=user.email, 
        password_hash=hashed_password,
        is_approved=is_approved,
        role="admin" if is_approved else "user"
    )
    if is_approved:
        new_user.approved_at = datetime.utcnow()
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval. Please contact admin.")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/pending-users", response_model=list[ApprovalResponse])
def get_pending_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    users = db.query(User).filter(User.is_approved == False).all()
    return [ApprovalResponse(
        id=u.id,
        email=u.email,
        is_approved=u.is_approved,
        created_at=u.created_at.isoformat()
    ) for u in users]

@router.post("/approve/{user_id}")
def approve_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_approved = True
    user.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User {user.email} approved"}

@router.post("/reject/{user_id}")
def reject_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.email} rejected"}
