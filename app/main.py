from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api.routes import router as api_router
from app.core.config import settings
import os

app = FastAPI(
    title="Autonomous Research Assistant",
    description="Agentic AI Researcher with RAG and FastAPI",
    version="1.0.0"
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- API ROUTES ----------------
app.include_router(api_router, prefix="/api/v1")

# ---------------- STATIC FILES ----------------
app.mount(
    "/",
    StaticFiles(directory=settings.STATIC_DIR, html=True),
    name="static"
)

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
