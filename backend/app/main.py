"""
app/main.py

FastAPI application entry point.
Mounts the API router under /api (matches the frontend vite proxy ->
http://127.0.0.1:8000). Run: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.upload_routes import router as upload_router  # 👈 NEW IMPORT
from .core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="4.1.0",
    description="AI-assisted digital forensic investigation platform (dev build).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
app.include_router(upload_router)  # 👈 NEW ROUTER (already has /api/upload prefix)

@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs", "api": settings.api_prefix}

@app.get("/health")
async def health():
    return {"status": "healthy"}