"""
INVESTCOPS AI - FastAPI Backend
Main application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.session import init_db
from app.routes import agents, auth, cases, compat, evidence, reports, results

setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic Digital Investigation Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(agents.router)
app.include_router(results.router)
app.include_router(reports.router)
app.include_router(compat.router)


@app.get("/")
async def root():
    return {
        "service": "INVESTCOPS AI Backend",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }