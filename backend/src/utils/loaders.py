import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document

try:
    from langchain_pymupdf4llm import PyMuPDF4LLMLoader
except ImportError:
    PyMuPDF4LLMLoader = None
try:
    from langchain_community.document_loaders import UnstructuredFileLoader, UnstructuredWordDocumentLoader, TextLoader
except ImportError:
    UnstructuredFileLoader = UnstructuredWordDocumentLoader = TextLoader = None

def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    m = {".pdf": "pdf", ".docx": "docx", ".doc": "docx", ".xlsx": "xlsx", ".pptx": "pptx", ".txt": "txt", ".md": "txt"}
    return m.get(ext, "unknown")

def load_documents_from_file_sync(file_path: str, file_type: str) -> List[Document]:
    if not os.path.isfile(file_path):
        raise ValueError(f"File not found: {file_path}")
    if file_type == "pdf" and PyMuPDF4LLMLoader:
        return PyMuPDF4LLMLoader(file_path).load()
    if file_type == "docx" and UnstructuredWordDocumentLoader:
        return UnstructuredWordDocumentLoader(file_path).load()
    if file_type == "txt" and TextLoader:
        return TextLoader(file_path).load()
    if UnstructuredFileLoader:
        return UnstructuredFileLoader(file_path).load()
    raise ValueError(f"Unsupported type or missing loader: {file_type}")
