from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import markdown
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

@app.get("/api-guide", response_class=HTMLResponse)
def api_guide():
    """API 가이드 문서를 HTML로 렌더링"""
    guide_path = Path(__file__).parent / "static" / "api-guide.md"
    if guide_path.exists():
        md_content = guide_path.read_text(encoding="utf-8")
        html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Wadio API 가이드</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }}
                h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
                h2 {{ color: #4CAF50; margin-top: 30px; }}
                h3 {{ color: #666; }}
                code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 14px; }}
                pre {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                pre code {{ background: none; padding: 0; color: inherit; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                a {{ color: #4CAF50; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .back-link {{ display: inline-block; margin-bottom: 20px; background: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; }}
                .back-link:hover {{ background: #45a049; }}
            </style>
        </head>
        <body>
            <a href="/" class="back-link">← 홈으로</a>
            {html_content}
        </body>
        </html>
        """
    return HTMLResponse(content="<h1>API 가이드를 찾을 수 없습니다</h1>", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wadio.main:app", host="0.0.0.0", port=21302, reload=True)
