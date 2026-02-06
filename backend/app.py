"""Questionnaire Agent API."""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import Base, engine
from src.models.db_models import (
    DocumentRegistry, Project, Question, Answer, Citation,
    Request, EvaluationRun, EvaluationResult,
)
from src.api.documents import router as documents_router
from src.api.requests import router as requests_router
from src.api.projects import router as projects_router
from src.api.answers import router as answers_router
from src.api.evaluation import router as evaluation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Questionnaire Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all in dev so frontend shows "connected" from any origin
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router, prefix="/api")
app.include_router(requests_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(answers_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
