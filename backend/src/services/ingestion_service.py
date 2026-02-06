from typing import Optional, Tuple
from sqlalchemy.orm import Session
from src.indexing.pipeline import index_document
from src.models.db_models import DocumentRegistry, Project, ProjectStatusEnum

def run_indexing_and_registry(db: Session, file_path: str, filename: str, document_id: Optional[str] = None) -> Tuple[str, int, int]:
    doc_id, sec_count, cit_count = index_document(file_path, filename, document_id)
    reg = db.query(DocumentRegistry).filter(DocumentRegistry.document_id == doc_id).first()
    if reg:
        reg.chunk_count_section, reg.chunk_count_citation, reg.filename = sec_count, cit_count, filename
    else:
        db.add(DocumentRegistry(document_id=doc_id, filename=filename, chunk_count_section=sec_count, chunk_count_citation=cit_count))
    db.commit()
    db.query(Project).filter(Project.scope == "ALL_DOCS", Project.status != ProjectStatusEnum.OUTDATED).update({Project.status: ProjectStatusEnum.OUTDATED}, synchronize_session=False)
    db.commit()
    return doc_id, sec_count, cit_count
