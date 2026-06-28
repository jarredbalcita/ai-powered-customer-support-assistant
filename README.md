# AI-powered customer support assistant

This workspace now includes:
- A FastAPI backend in the backend folder
- A Flutter frontend in the frontend folder

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

The Flutter app calls the backend at http://127.0.0.1:8000/api/message.
