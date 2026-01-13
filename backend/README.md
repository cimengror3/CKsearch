# CKSEARCH API Backend

FastAPI backend for CKSEARCH license management.

## Setup Local

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Deploy to Railway

1. Create new project on Railway
2. Add PostgreSQL database
3. Connect GitHub repo (or use Railway CLI)
4. Set environment variables
5. Deploy!

## Environment Variables

```
DATABASE_URL=postgresql://user:pass@host:port/db
ADMIN_SECRET=your-admin-secret
JWT_SECRET=your-jwt-secret
CURRENT_VERSION=1.0.0
```
