import enum
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from src.core.database import Base


class ProjectStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    READY = "READY"
    OUTDATED = "OUTDATED"
    GENERATING = "GENERATING"
    COMPLETE = "COMPLETE"


class AnswerStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    MANUAL_UPDATED = "MANUAL_UPDATED"
    MISSING_DATA = "MISSING_DATA"


class RequestTypeEnum(str, enum.Enum):
    create_project = "create_project"
    update_project = "update_project"
    index_document = "index_document"
    generate_answers = "generate_answers"


class RequestStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentRegistry(Base):
    __tablename__ = "document_registry"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())
    chunk_count_section = Column(Integer, default=0)
    chunk_count_citation = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(512), nullable=False)
    questionnaire_document_id = Column(String(255), nullable=True, index=True)
    scope = Column(String(512), nullable=False, default="ALL_DOCS")
    status = Column(Enum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    questions = relationship("Question", back_populates="project", order_by="Question.order_index", cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="project", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(128), nullable=True)
    section_title = Column(String(512), nullable=True)
    question_text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    project = relationship("Project", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    evaluation_results = relationship("EvaluationResult", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text, nullable=True)
    is_answerable = Column(Integer, nullable=False, default=1)
    confidence_score = Column(Float, nullable=True)
    status = Column(Enum(AnswerStatusEnum), nullable=False, default=AnswerStatusEnum.PENDING, index=True)
    ai_answer_text = Column(Text, nullable=True)
    manual_answer_text = Column(Text, nullable=True)
    human_answer_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    question = relationship("Question", back_populates="answer")
    citations = relationship("Citation", back_populates="answer", order_by="Citation.order_index", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(255), nullable=True)
    document_id = Column(String(255), nullable=True)
    snippet = Column(Text, nullable=True)
    bounding_box_ref = Column(String(256), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    answer = relationship("Answer", back_populates="citations")


class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(RequestTypeEnum), nullable=False, index=True)
    status = Column(Enum(RequestStatusEnum), nullable=False, default=RequestStatusEnum.PENDING, index=True)
    entity_id = Column(String(255), nullable=True, index=True)
    result_payload = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    project = relationship("Project", back_populates="evaluation_runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_answer = Column(Text, nullable=True)
    human_answer = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)
    details = Column(Text, nullable=True)
    run = relationship("EvaluationRun", back_populates="results")
    question = relationship("Question", back_populates="evaluation_results")
