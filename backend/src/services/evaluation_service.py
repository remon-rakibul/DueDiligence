import re
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from src.models.db_models import EvaluationRun, EvaluationResult, Answer, Question

def _keyword_overlap(ai: str, human: str) -> float:
    def tokens(t): return set(re.sub(r"[^\w\s]", " ", (t or "").lower()).split())
    a_set, b_set = tokens(ai), tokens(human)
    if not a_set and not b_set: return 1.0
    if not a_set or not b_set: return 0.0
    return len(a_set & b_set) / max(len(a_set), len(b_set))

def run_evaluation(db: Session, project_id: int, use_embeddings: bool = True) -> EvaluationRun:
    run = EvaluationRun(project_id=project_id)
    db.add(run)
    db.flush()
    questions = db.query(Question).filter(Question.project_id == project_id).order_by(Question.order_index).all()
    embeddings = OpenAIEmbeddings() if use_embeddings else None
    for q in questions:
        ans = db.query(Answer).filter(Answer.question_id == q.id).first()
        if not ans or not ans.human_answer_text:
            continue
        ai_text, human_text = ans.ai_answer_text or "", ans.human_answer_text or ""
        kw = _keyword_overlap(ai_text, human_text)
        if use_embeddings and embeddings:
            vecs = embeddings.embed_documents([ai_text, human_text])
            if len(vecs) == 2:
                a, b = vecs[0], vecs[1]
                dot = sum(x * y for x, y in zip(a, b))
                na, nb = sum(x * x for x in a) ** 0.5, sum(y * y for y in b) ** 0.5
                sem = max(0, min(1, (dot / (na * nb) + 1) / 2)) if na and nb else 0
                score, details = 0.5 * sem + 0.5 * kw, f"semantic={sem:.3f}, keyword={kw:.3f}"
            else:
                score, details = kw, f"keyword={kw:.3f}"
        else:
            score, details = kw, f"keyword={kw:.3f}"
        db.add(EvaluationResult(run_id=run.id, question_id=q.id, ai_answer=ai_text, human_answer=human_text, similarity_score=round(score, 4), details=details))
    db.commit()
    db.refresh(run)
    return run
