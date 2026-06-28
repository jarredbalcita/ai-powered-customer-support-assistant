# FastAPI backend

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/message
