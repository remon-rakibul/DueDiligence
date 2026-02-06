import json
import re
from typing import List, Tuple
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session
from src.models.db_models import Answer, Citation, Question, AnswerStatusEnum
from src.storage.vector_store import get_vector_store_service

SYSTEM_PROMPT = """Answer the question using ONLY the provided context. If the context does not contain enough information, set "answerable" to false.
Output a JSON object with keys: "answer" (string), "answerable" (boolean), "confidence" (float 0-1), "citations" (array of {"chunk_id": "...", "snippet": "..."})."""

def _build_context(docs):
    return "\n\n---\n\n".join(f"[chunk_{i}]\n{d.page_content}" for i, d in enumerate(docs))

def _parse_llm_json(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0)) if m else {"answer": text, "answerable": True, "confidence": 0.5, "citations": []}

def generate_answer_for_question(db: Session, question_id: int) -> Tuple[Answer, List[Citation]]:
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise ValueError("Question not found")
    vs = get_vector_store_service()
    retriever = vs.get_retriever(search_kwargs={"k": 6})
    docs = retriever.invoke(q.question_text)
    if not docs:
        answer = Answer(question_id=q.id, answer_text="No relevant documents found.", is_answerable=0, confidence_score=0.0, status=AnswerStatusEnum.PENDING, ai_answer_text="No relevant documents found.")
        db.add(answer)
        db.flush()
        return answer, []
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    content = llm.invoke([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Context:\n{_build_context(docs)}\n\nQuestion: {q.question_text}\n\nOutput JSON only."}]).content
    try:
        data = _parse_llm_json(content)
    except json.JSONDecodeError:
        data = {"answer": content, "answerable": True, "confidence": 0.5, "citations": []}
    answer = Answer(question_id=q.id, answer_text=data.get("answer", ""), is_answerable=1 if data.get("answerable", True) else 0, confidence_score=float(data.get("confidence", 0.5)), status=AnswerStatusEnum.PENDING, ai_answer_text=data.get("answer", ""))
    db.add(answer)
    db.flush()
    citations_list = []
    for i, c in enumerate(data.get("citations") or []):
        if isinstance(c, dict):
            doc_id = next((d.metadata.get("document_id") for d in docs if d.metadata.get("document_id")), None)
            citations_list.append(Citation(answer_id=answer.id, chunk_id=str(c.get("chunk_id", c.get("id", ""))), document_id=doc_id, snippet=(c.get("snippet", "") or "")[:2000], order_index=i))
    for cit in citations_list:
        db.add(cit)
    db.commit()
    db.refresh(answer)
    return answer, citations_list
