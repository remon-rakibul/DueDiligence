import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from src.core.config import settings
from src.models.db_models import Project, Question, Request, RequestTypeEnum, RequestStatusEnum, ProjectStatusEnum
from src.models.schemas import RequestResponse, RequestType, RequestStatus
from src.services.project_service import create_project_from_parsed
from src.services.questionnaire_parser import parse_questionnaire_file
from src.services.ingestion_service import run_indexing_and_registry
from src.storage.database import get_db, SessionLocal

router = APIRouter(prefix="/projects", tags=["projects"])

def _save_upload(file_content: bytes, filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    name = Path(filename).name.replace("/", "").replace("..", "")[:255]
    path = os.path.join(settings.UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(file_content)
    return path

def _create_project_task(request_id: int, file_path: str, filename: str, name: str):
    db = SessionLocal()
    try:
        req = db.query(Request).filter(Request.id == request_id).first()
        if not req or req.status != RequestStatusEnum.PENDING:
            return
        req.status = RequestStatusEnum.RUNNING
        db.commit()
        doc_id, _, _ = run_indexing_and_registry(db, file_path, filename, None)
        parsed = parse_questionnaire_file(file_path, filename)
        project = create_project_from_parsed(db, name=name, parsed=parsed, questionnaire_document_id=doc_id, scope="ALL_DOCS")
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.COMPLETED
            req.entity_id = str(project.id)
            req.result_payload = f'{{"project_id":{project.id}}}'
            req.error_message = None
            db.commit()
    except Exception as e:
        db.rollback()
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.FAILED
            req.error_message = str(e)
            db.commit()
    finally:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass
        db.close()

@router.post("/create-async", response_model=RequestResponse)
async def create_project_async(background_tasks: BackgroundTasks, name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    path = _save_upload(content, file.filename)
    req = Request(type=RequestTypeEnum.create_project, status=RequestStatusEnum.PENDING, entity_id=None)
    db.add(req)
    db.commit()
    db.refresh(req)
    background_tasks.add_task(_create_project_task, req.id, path, file.filename, name.strip())
    return RequestResponse(id=req.id, type=RequestType(req.type.value), status=RequestStatus(req.status.value), entity_id=req.entity_id, result_payload=req.result_payload, error_message=req.error_message, created_at=req.created_at)

@router.get("/list", response_model=list)
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return [{"id": p.id, "name": p.name, "status": p.status.value, "scope": p.scope, "created_at": p.created_at.isoformat() if p.created_at else None, "updated_at": p.updated_at.isoformat() if p.updated_at else None} for p in projects]

@router.get("/{project_id}", response_model=dict)
def get_project_info(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    questions = db.query(Question).filter(Question.project_id == project_id).order_by(Question.order_index).all()
    return {"id": project.id, "name": project.name, "questionnaire_document_id": project.questionnaire_document_id, "scope": project.scope, "status": project.status.value, "created_at": project.created_at.isoformat() if project.created_at else None, "updated_at": project.updated_at.isoformat() if project.updated_at else None, "questions": [{"id": q.id, "section_id": q.section_id, "section_title": q.section_title, "question_text": q.question_text, "order_index": q.order_index} for q in questions]}

@router.get("/{project_id}/status")
def get_project_status(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "status": project.status.value}


def _update_project_task(request_id: int, project_id: int, name: Optional[str], scope: Optional[str]):
    db = SessionLocal()
    try:
        req = db.query(Request).filter(Request.id == request_id).first()
        if not req or req.status != RequestStatusEnum.PENDING:
            return
        req.status = RequestStatusEnum.RUNNING
        db.commit()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            req.status = RequestStatusEnum.FAILED
            req.error_message = "Project not found"
            db.commit()
            return
        if name is not None:
            project.name = name
        if scope is not None:
            project.scope = scope
        req.status = RequestStatusEnum.COMPLETED
        req.entity_id = str(project_id)
        req.result_payload = f'{{"project_id":{project_id}}}'
        db.commit()
    except Exception as e:
        db.rollback()
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.FAILED
            req.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/update-async", response_model=RequestResponse)
async def update_project_async(
    background_tasks: BackgroundTasks,
    project_id: int,
    name: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if name is None and scope is None:
        raise HTTPException(status_code=400, detail="Provide at least one of name or scope")
    req = Request(type=RequestTypeEnum.update_project, status=RequestStatusEnum.PENDING, entity_id=str(project_id))
    db.add(req)
    db.commit()
    db.refresh(req)
    background_tasks.add_task(_update_project_task, req.id, project_id, name.strip() if name else None, scope.strip() if scope else None)
    return RequestResponse(id=req.id, type=RequestType(req.type.value), status=RequestStatus(req.status.value), entity_id=req.entity_id, result_payload=req.result_payload, error_message=req.error_message, created_at=req.created_at)
