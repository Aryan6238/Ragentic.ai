from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(
    title="Autonomous Research Assistant",
    description="Agentic AI Researcher with RAG and FastAPI",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(api_router, prefix="/api/v1")

# Static Files (Frontend)
app.mount("/", StaticFiles(directory=settings.STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import sys
    import io
    
    # Fix encoding for Windows terminal
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "="*60)
    print("RAGentic.ai Server Starting...")
    print("="*60)
    print(f"Server running at: http://localhost:8000")
    print(f"API Documentation: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
