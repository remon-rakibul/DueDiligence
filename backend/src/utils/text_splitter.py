from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _split(documents: List[Document], chunk_size: int, chunk_overlap: int, chunk_type: str) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len, separators=["\n\n", "\n", ". ", " ", ""])
    out = []
    for doc in splitter.split_documents(documents):
        meta = dict(doc.metadata)
        meta["chunk_type"] = chunk_type
        out.append(Document(page_content=doc.page_content, metadata=meta))
    return out

def split_into_section_chunks(documents: List[Document]) -> List[Document]:
    return _split(documents, 1000, 200, "section")

def split_into_citation_chunks(documents: List[Document]) -> List[Document]:
    return _split(documents, 400, 50, "citation")
