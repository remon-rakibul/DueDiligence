from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProjectStatus(str, Enum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    READY = "READY"
    OUTDATED = "OUTDATED"
    GENERATING = "GENERATING"
    COMPLETE = "COMPLETE"


class AnswerStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    MANUAL_UPDATED = "MANUAL_UPDATED"
    MISSING_DATA = "MISSING_DATA"


class RequestType(str, Enum):
    create_project = "create_project"
    update_project = "update_project"
    index_document = "index_document"
    generate_answers = "generate_answers"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CitationResponse(BaseModel):
    id: int
    answer_id: int
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    snippet: Optional[str] = None
    bounding_box_ref: Optional[str] = None
    order_index: int
    class Config:
        from_attributes = True


class RequestResponse(BaseModel):
    id: int
    type: RequestType
    status: RequestStatus
    entity_id: Optional[str] = None
    result_payload: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class DocumentRegistryResponse(BaseModel):
    id: int
    document_id: str
    filename: str
    indexed_at: datetime
    chunk_count_section: int
    chunk_count_citation: int
    created_at: datetime
    class Config:
        from_attributes = True


class AnswerUpdate(BaseModel):
    status: Optional[AnswerStatus] = None
    manual_answer_text: Optional[str] = None
    human_answer_text: Optional[str] = None


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: Optional[str] = None
    is_answerable: bool = True
    confidence_score: Optional[float] = None
    status: AnswerStatus
    ai_answer_text: Optional[str] = None
    manual_answer_text: Optional[str] = None
    human_answer_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    citations: List[CitationResponse] = []
    @field_validator("is_answerable", mode="before")
    @classmethod
    def is_answerable_to_bool(cls, v):
        return bool(v) if v is not None else True
    class Config:
        from_attributes = True


class GenerateSingleAnswerResponse(BaseModel):
    answer_id: int
    answer_text: Optional[str] = None
    is_answerable: bool
    confidence_score: Optional[float] = None
    citations: List[CitationResponse] = []
