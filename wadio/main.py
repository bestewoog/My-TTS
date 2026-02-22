from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from wadio.database import init_db
from wadio.api import auth, voice_files, finetune, speakers, tts

app = FastAPI(title="Wadio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth.router, prefix="/api")
app.include_router(voice_files.router, prefix="/api")
app.include_router(finetune.router, prefix="/api")
app.include_router(speakers.router, prefix="/api")
app.include_router(tts.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Wadio API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=21302)
