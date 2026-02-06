import uuid
from typing import Optional, Tuple
from src.storage.vector_store import get_vector_store_service
from src.utils.loaders import get_file_type, load_documents_from_file_sync
from src.utils.text_splitter import split_into_section_chunks, split_into_citation_chunks

def index_document(file_path: str, filename: str, document_id: Optional[str] = None) -> Tuple[str, int, int]:
    doc_id = document_id or str(uuid.uuid4())
    file_type = get_file_type(filename)
    raw_docs = load_documents_from_file_sync(file_path, file_type)
    if not raw_docs:
        raise ValueError(f"No content from {filename}")
    for d in raw_docs:
        d.metadata["document_id"] = doc_id
        d.metadata["filename"] = filename
    section_chunks = split_into_section_chunks(raw_docs)
    citation_chunks = split_into_citation_chunks(raw_docs)
    section_ids = [f"{doc_id}_sec_{i}" for i in range(len(section_chunks))]
    citation_ids = [f"{doc_id}_cit_{i}" for i in range(len(citation_chunks))]
    vs = get_vector_store_service()
    vs.add_documents(section_chunks, ids=section_ids)
    vs.add_documents(citation_chunks, ids=citation_ids)
    return doc_id, len(section_chunks), len(citation_chunks)
