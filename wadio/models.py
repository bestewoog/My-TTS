from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from wadio.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

class VoiceFile(Base):
    __tablename__ = "voice_files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    transcript = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FineTuneJob(Base):
    __tablename__ = "finetune_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    speaker_name = Column(String)
    status = Column(String, default="queued")
    config = Column(JSON)
    voice_file_ids = Column(String)
    checkpoint_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Speaker(Base):
    __tablename__ = "speakers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    speaker_id = Column(Integer)
    model_path = Column(String)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
