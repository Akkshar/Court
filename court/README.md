# Chef’s Court of Justice (Backend)

FastAPI + PostgreSQL backend with:
- JWT auth (signup/login)
- Role-based access control (Plaintiff/Defendant/Juror/Judge)
- Case submissions (argument + evidence plaintext)
- Judge review workflow (approve/reject/edit/delete)
- Jury voting (vote once per case; results tally)

## Quick start (Docker)
1) Copy env file:
```bash
cp .env.example .env
```

2) Start Postgres + API:
```bash
docker compose up --build
```

3) Run DB migrations inside the api container:
```bash
docker compose exec api alembic upgrade head
```

4) Open API docs:
- Swagger: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Local dev (no Docker)
Prereqs: Python 3.11+, PostgreSQL

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Roles
- PLAINTIFF / DEFENDANT: submit arguments/evidence
- JUROR: view *approved* submissions; vote once per case
- JUDGE: approve/reject/edit/delete any submission; view results

## Notes
- Evidence is stored as plaintext in `evidence_text` for simplicity.
- “Vote once” is enforced in the DB via unique constraint (case_id, juror_user_id).
