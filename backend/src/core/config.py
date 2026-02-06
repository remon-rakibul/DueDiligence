from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/duediligence"
    VECTOR_STORE_TABLE_NAME: str = "document_chunks"
    VECTOR_SIZE: int = 1536
    OPENAI_API_KEY: str = ""
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024
    UPLOAD_DIR: str = "/tmp/questionnaire_uploads"

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        extra = "ignore"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
