# Questionnaire Agent — Due Diligence Demo

Full-stack Questionnaire Agent: ingest and index documents, parse questionnaires, auto-generate answers with citations, review workflow, and evaluation against human ground truth. See `docs/QUESTIONNAIRE_AGENT_TASKS.md` for scope and acceptance criteria.

## Prerequisites

- **Python 3.12+** and **Node 18+**
- **PostgreSQL 16+** with the **pgvector** extension
- **OpenAI API key** (for embeddings and answer generation)

## Quick start

### 1. Clone and backend setup

From the project root:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Database

**Option A — Docker (recommended)**

```bash
docker compose up -d
```

Uses image `pgvector/pgvector:pg16`. Database: `duediligence`, user: `postgres`, password: `postgres`. If host port 5432 is in use, the compose file maps DB to **5433** and backend to **8001**.

**Option B — Local PostgreSQL**

```bash
createdb duediligence
psql -d duediligence -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

### 3. Environment

Create `backend/.env` (see `backend/.env.example`):

- **DATABASE_URL** — e.g. `postgresql://postgres:postgres@localhost:5432/duediligence` (use port 5433 if Docker DB is on 5433).
- **OPENAI_API_KEY** — required for indexing and answer generation.

### 4. Start backend

```bash
cd backend
../venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

Or from project root: `venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000` (if imports fail, use the `cd backend` form above).

Backend: **http://localhost:8000** — health: **http://localhost:8000/health**.

### 5. Start frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The app proxies `/api` and `/health` to the backend.

### 6. Smoke test (optional)

With the backend running on port 8000:

```bash
./scripts/smoke_test.sh
```

Uses `data/` by default: indexes a reference PDF, creates a project from the ILPA questionnaire, generates answers, indexes a second document, and checks that the project becomes OUTDATED. Requires a valid `OPENAI_API_KEY` in `backend/.env`; indexing and answer generation can take several minutes.

**Against Docker backend (port 8001):**

```bash
API=http://localhost:8001 ./scripts/smoke_test.sh
```

Ensure `OPENAI_API_KEY` is set in `backend/.env` so the backend container can call OpenAI.

## Dataset

- **Questionnaire:** `data/ILPA_Due_Diligence_Questionnaire_v1.2.pdf` — use when creating a project.
- **Reference docs:** `data/` MiniMax PDFs — upload via **Documents** to index, then generate answers for a project scoped to all docs.

## Successfully running the codebase

You have a successful run when:

1. **Backend** — `curl http://localhost:8000/health` returns `{"status":"ok"}`.
2. **Frontend** — http://localhost:5173 shows “Backend: connected” and the nav (Projects, Create project, Documents, Request status).
3. **Flow** — You can create a project (upload ILPA questionnaire PDF), open it, run “Generate all answers”, review answers and set human answers for evaluation, then open **Evaluation report** and run evaluation to see AI vs human scores.

If the backend fails to start, check `DATABASE_URL` and that PostgreSQL has the `vector` extension. If indexing or generation fails with 401, set `OPENAI_API_KEY` in `backend/.env`.

## Docs

- **docs/QUESTIONNAIRE_AGENT_TASKS.md** — Task scope and acceptance criteria.
- **backend/README.md** — Backend structure and APIs.
- **frontend/README.md** — Frontend screens and modules.
