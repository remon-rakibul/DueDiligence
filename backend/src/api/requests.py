from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.db_models import Request
from src.models.schemas import RequestResponse, RequestType, RequestStatus
from src.storage.database import get_db

router = APIRouter(prefix="/requests", tags=["requests"])

@router.get("/{request_id}", response_model=RequestResponse)
def get_request_status(request_id: int, db: Session = Depends(get_db)):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return RequestResponse(id=req.id, type=RequestType(req.type.value), status=RequestStatus(req.status.value), entity_id=req.entity_id, result_payload=req.result_payload, error_message=req.error_message, created_at=req.created_at)
