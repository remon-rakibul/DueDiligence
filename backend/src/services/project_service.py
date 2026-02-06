from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.db_models import Project, Question, ProjectStatusEnum
from src.services.questionnaire_parser import ParsedQuestion

def create_project_from_parsed(db: Session, name: str, parsed: List[ParsedQuestion], questionnaire_document_id: Optional[str] = None, scope: str = "ALL_DOCS") -> Project:
    project = Project(name=name, questionnaire_document_id=questionnaire_document_id, scope=scope, status=ProjectStatusEnum.READY)
    db.add(project)
    db.flush()
    for pq in parsed:
        db.add(Question(project_id=project.id, section_id=pq.section_id, section_title=pq.section_title, question_text=pq.question_text, order_index=pq.order_index))
    db.commit()
    db.refresh(project)
    return project
