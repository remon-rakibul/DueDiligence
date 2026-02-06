import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.db_models import Answer, Citation, Question, Project, Request, RequestTypeEnum, RequestStatusEnum, ProjectStatusEnum, AnswerStatusEnum
from src.models.schemas import AnswerResponse, AnswerStatus, CitationResponse, GenerateSingleAnswerResponse, RequestResponse, RequestType, RequestStatus, AnswerUpdate
from src.services.answer_service import generate_answer_for_question
from src.storage.database import get_db, SessionLocal

router = APIRouter(prefix="/answers", tags=["answers"])

def _answer_to_response(a: Answer) -> AnswerResponse:
    cit_list = list(a.citations) if a.citations else []
    return AnswerResponse(id=a.id, question_id=a.question_id, answer_text=a.manual_answer_text if a.status == AnswerStatusEnum.MANUAL_UPDATED else (a.ai_answer_text or a.answer_text), is_answerable=bool(a.is_answerable), confidence_score=a.confidence_score, status=AnswerStatus(a.status.value), ai_answer_text=a.ai_answer_text, manual_answer_text=a.manual_answer_text, human_answer_text=a.human_answer_text, created_at=a.created_at, updated_at=a.updated_at, citations=[CitationResponse(id=c.id, answer_id=c.answer_id, chunk_id=c.chunk_id, document_id=c.document_id, snippet=c.snippet, bounding_box_ref=c.bounding_box_ref, order_index=c.order_index) for c in cit_list])

@router.post("/generate-single", response_model=GenerateSingleAnswerResponse)
def generate_single_answer(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.query(Answer).filter(Answer.question_id == question_id).delete()
    db.commit()
    answer, citations = generate_answer_for_question(db, question_id)
    return GenerateSingleAnswerResponse(answer_id=answer.id, answer_text=answer.answer_text, is_answerable=bool(answer.is_answerable), confidence_score=answer.confidence_score, citations=[CitationResponse(id=c.id, answer_id=c.answer_id, chunk_id=c.chunk_id, document_id=c.document_id, snippet=c.snippet, bounding_box_ref=c.bounding_box_ref, order_index=c.order_index) for c in citations])

def _generate_all_task(request_id: int, project_id: int):
    db = SessionLocal()
    try:
        req = db.query(Request).filter(Request.id == request_id).first()
        if not req or req.status != RequestStatusEnum.PENDING:
            return
        req.status = RequestStatusEnum.RUNNING
        db.commit()
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.status = ProjectStatusEnum.GENERATING
            db.commit()
        for q in db.query(Question).filter(Question.project_id == project_id).order_by(Question.order_index).all():
            db.query(Answer).filter(Answer.question_id == q.id).delete()
            db.commit()
            generate_answer_for_question(db, q.id)
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.status = ProjectStatusEnum.COMPLETE
            db.commit()
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.COMPLETED
            req.entity_id = str(project_id)
            req.result_payload = f'{{"project_id":{project_id}}}'
            db.commit()
    except Exception as e:
        db.rollback()
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.status = ProjectStatusEnum.OUTDATED
            db.commit()
        req = db.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = RequestStatusEnum.FAILED
            req.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.post("/generate-all-async", response_model=RequestResponse)
def generate_all_answers_async(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    req = Request(type=RequestTypeEnum.generate_answers, status=RequestStatusEnum.PENDING, entity_id=str(project_id))
    db.add(req)
    db.commit()
    db.refresh(req)
    background_tasks.add_task(_generate_all_task, req.id, project_id)
    return RequestResponse(id=req.id, type=RequestType(req.type.value), status=RequestStatus(req.status.value), entity_id=req.entity_id, result_payload=req.result_payload, error_message=req.error_message, created_at=req.created_at)

@router.post("/update", response_model=AnswerResponse)
def update_answer(answer_id: int, body: AnswerUpdate, db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    if body.status is not None:
        answer.status = AnswerStatusEnum(body.status.value)
        if body.status == AnswerStatus.MANUAL_UPDATED and (body.manual_answer_text or answer.manual_answer_text):
            answer.answer_text = body.manual_answer_text or answer.manual_answer_text
    if body.manual_answer_text is not None:
        answer.manual_answer_text = body.manual_answer_text
    if body.human_answer_text is not None:
        answer.human_answer_text = body.human_answer_text
    db.commit()
    db.refresh(answer)
    return _answer_to_response(answer)

@router.get("/by-question/{question_id}", response_model=AnswerResponse | None)
def get_answer_by_question(question_id: int, db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.question_id == question_id).first()
    return _answer_to_response(answer) if answer else None

@router.get("/by-project/{project_id}", response_model=list)
def list_answers_by_project(project_id: int, db: Session = Depends(get_db)):
    q_ids = [r[0] for r in db.query(Question.id).filter(Question.project_id == project_id).all()]
    return [_answer_to_response(a) for a in db.query(Answer).filter(Answer.question_id.in_(q_ids)).all()]
