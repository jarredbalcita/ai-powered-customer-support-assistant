# FastAPI backend

See the root [README.md](../README.md) for full setup, architecture, and API documentation.

## Run locally

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET  http://127.0.0.1:8000/health` — liveness check
- `POST http://127.0.0.1:8000/chat`  — main chat endpoint
