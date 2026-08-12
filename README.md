# InvestCops AI — Forensic Intelligence Platform

AI-assisted digital forensic investigation platform. FastAPI backend + React (Liquid Glass) frontend.

## Layout

| Folder | What it is |
|---|---|
| `frontend/` | React + Tailwind v4 dashboard (NoteNext Liquid Glass UI: dashboard, cases, evidence upload, AI processing, results, reports, analytics, deepfake detector, APK scanner, FIR converter, USB field extractor) |
| `backend/` | FastAPI app (`app/main.py`) serving the dashboard API under `/api` |
| `ai-agents/` | Agent pipeline (Ollama-based, per-agent modules) |
| `forensics/` | Forensic utility modules (skeleton) |

## Run locally (dev)

**Backend** (port 8000):

```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (port 5173):

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## API endpoints (used by the frontend)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | service status |
| POST | `/api/fir/convert` | informal text → FIR draft (Ollama, mock fallback) |
| POST | `/api/blockchain/notarize` | SHA-256 evidence → ledger record |
| POST | `/api/blockchain/verify` | verify a hash against the ledger |
| GET | `/api/blockchain/ledger` | full evidence ledger |
| GET | `/api/field/status` | ADB device status (mock when offline) |
| GET | `/api/field/list` | past field extraction backups |
| POST | `/api/field/extract` | one-click logical extraction (mock when offline) |

## Run with Docker

```
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (docs at /docs)
- PostgreSQL: localhost:5432 · Neo4j: localhost:7474 (bolt 7687)

The backend runs standalone without Postgres/Neo4j; they are only used when `DATABASE_URL` / `NEO4J_URI` are set.
