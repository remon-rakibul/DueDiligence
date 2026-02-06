from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.models.db_models import EvaluationRun, EvaluationResult, Project
from src.services.evaluation_service import run_evaluation
from src.storage.database import get_db

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/run", response_model=dict)
def create_evaluation_run(project_id: int, db: Session = Depends(get_db)):
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    run = run_evaluation(db, project_id, use_embeddings=True)
    results = db.query(EvaluationResult).filter(EvaluationResult.run_id == run.id).all()
    return {"id": run.id, "project_id": run.project_id, "created_at": run.created_at.isoformat() if run.created_at else None, "results": [{"id": r.id, "run_id": r.run_id, "question_id": r.question_id, "ai_answer": r.ai_answer, "human_answer": r.human_answer, "similarity_score": r.similarity_score, "details": r.details} for r in results]}

@router.get("/report")
def get_evaluation_report(project_id: int, run_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    run = db.query(EvaluationRun).filter(EvaluationRun.project_id == project_id).order_by(EvaluationRun.created_at.desc()).first() if run_id is None else db.query(EvaluationRun).filter(EvaluationRun.id == run_id, EvaluationRun.project_id == project_id).first()
    if not run:
        return {"project_id": project_id, "run_id": run_id, "message": "No evaluation run found", "results": [], "aggregate_score": None}
    results = db.query(EvaluationResult).filter(EvaluationResult.run_id == run.id).all()
    scores = [r.similarity_score for r in results if r.similarity_score is not None]
    aggregate = sum(scores) / len(scores) if scores else None
    return {"project_id": project_id, "run_id": run.id, "created_at": run.created_at.isoformat() if run.created_at else None, "aggregate_score": round(aggregate, 4) if aggregate is not None else None, "results": [{"question_id": r.question_id, "ai_answer": r.ai_answer, "human_answer": r.human_answer, "similarity_score": r.similarity_score, "details": r.details} for r in results]}
