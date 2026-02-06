import os
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from src.core.config import settings
from src.models.db_models import Request, RequestTypeEnum, RequestStatusEnum, DocumentRegistry
from src.models.schemas import DocumentRegistryResponse, RequestResponse, RequestType, RequestStatus
from src.services.ingestion_service import run_indexing_and_registry
from src.storage.database import get_db, SessionLocal

router = APIRouter(prefix="/documents", tags=["documents"])

def _save_upload(file_content: bytes, filename: str) -> str:
    name = Path(filename).name.replace("/", "").replace("\\", "").replace("..", "")[:255]
    if not name.strip():
        raise ValueError("Invalid filename")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    path = os.path.join(settings.UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(file_content)
    return path

def _index_task(request_id: int, file_path: str, filename: str):
    db = SessionLocal()
    try:
        req = db.query(Request).filter(Request.id == request_id).first()
        if not req or req.status != RequestStatusEnum.PENDING:
            return
        req.status = RequestStatusEnum.RUNNING
        db.commit()
        doc_id, sec, cit = run_indexing_and_registry(db, file_path, filename, None)
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.COMPLETED
            req.entity_id = doc_id
            req.result_payload = f'{{"document_id":"{doc_id}","section_count":{sec},"citation_count":{cit}}}'
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

@router.post("/index-async", response_model=RequestResponse)
async def index_document_async(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    try:
        path = _save_upload(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    req = Request(type=RequestTypeEnum.index_document, status=RequestStatusEnum.PENDING, entity_id=None)
    db.add(req)
    db.commit()
    db.refresh(req)
    background_tasks.add_task(_index_task, req.id, path, file.filename)
    return RequestResponse(id=req.id, type=RequestType(req.type.value), status=RequestStatus(req.status.value), entity_id=req.entity_id, result_payload=req.result_payload, error_message=req.error_message, created_at=req.created_at)

@router.get("", response_model=list)
def list_documents(db: Session = Depends(get_db)):
    rows = db.query(DocumentRegistry).order_by(DocumentRegistry.indexed_at.desc()).all()
    return [DocumentRegistryResponse(id=r.id, document_id=r.document_id, filename=r.filename, indexed_at=r.indexed_at, chunk_count_section=r.chunk_count_section, chunk_count_citation=r.chunk_count_citation, created_at=r.created_at) for r in rows]
