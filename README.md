# Disha — Multilingual Genetic Counselling Chatbot

Disha is a sickle-cell-disease (SCD) counselling chatbot for the SickleSetu
platform, targeting tribal Maharashtra. It answers in **English, Hindi, and
Marathi**, with RAG-backed retrieval over a curated knowledge base, OCR-based
report summarisation, Punnett-square inheritance visualisation, and facility
lookup via Google Places.

Monorepo layout:

```
.
├── backend/    FastAPI + Qdrant + Groq + OCR.space + Google Places
├── frontend/   React + Vite + Tailwind + Zustand
├── render.yaml Backend blueprint — auto-deploys on push
└── frontend/vercel.json  Frontend config
```

---

## Architecture

| Layer          | Tech                                                        |
|----------------|-------------------------------------------------------------|
| Frontend       | React 18, Vite, Tailwind, Zustand                           |
| Backend        | FastAPI, Pydantic v2, uvicorn                               |
| LLM            | Groq (`llama-3.3-70b-versatile`)                            |
| Vector DB      | Qdrant Cloud                                                |
| Embeddings     | HuggingFace Inference — `BAAI/bge-m3`                       |
| Reranker       | HuggingFace Inference — `BAAI/bge-reranker-v2-m3`           |
| OCR (PDF/img)  | OCR.space REST API                                          |
| OCR (.docx)    | `python-docx` (local, no API)                               |
| Facility lookup| Google Places API v1                                        |
| Sessions       | SQLite (ephemeral on Render free tier — resets on restart)  |

---

## Local development

Prerequisites: Python 3.11+, Node 18+.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # fill in your API keys
uvicorn app.main:app --host 127.0.0.1 --port 8800 --reload
```

Required keys in `.env`:

- `GROQ_API_KEY` — [console.groq.com](https://console.groq.com/)
- `QDRANT_URL`, `QDRANT_API_KEY` — [cloud.qdrant.io](https://cloud.qdrant.io/)
- `HF_API_KEY` — [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- `OCR_SPACE_API_KEY` — [ocr.space/ocrapi/freekey](https://ocr.space/ocrapi/freekey)
- `GOOGLE_MAPS_API_KEY` — Places API v1 enabled in [Google Cloud Console](https://console.cloud.google.com/)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server runs on http://localhost:5175 and proxies `/api/*` to the backend
at `http://127.0.0.1:8800` (see `vite.config.ts`). No `.env` needed for local
dev.

---

## Deployment

The backend goes to **Render** and the frontend to **Vercel**. Both auto-deploy
from every push to `main`.

### Step 1 — Backend (Render)

1. Sign in to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** → **Blueprint** → select this GitHub repo.
3. Render reads `render.yaml` and provisions the `disha-backend` service on
   the free plan.
4. When prompted, fill the secret env vars (the ones marked `sync: false`):
   - `GROQ_API_KEY`
   - `QDRANT_URL`, `QDRANT_API_KEY`
   - `HF_API_KEY`
   - `OCR_SPACE_API_KEY`
   - `GOOGLE_MAPS_API_KEY`
   - `ADMIN_KEY` — any long random string
   - `FRONTEND_ORIGIN` — leave blank for now; set after Vercel deploy
5. Wait for the build to go green. Copy the service URL, e.g.
   `https://disha-backend.onrender.com`.

Health check: `https://<your-url>/api/v1/health` should return
`{"status":"ok","version":"..."}`.

> **Free-tier caveat:** Render's free web service spins down after 15 min idle.
> The next request takes 30–60 s to wake it. Chat sessions stored in SQLite
> are wiped on every restart/redeploy. For a production launch, upgrade to the
> Starter plan (~$7/mo) and attach a persistent disk, or migrate sessions to
> Upstash Redis / Neon Postgres.

### Step 2 — Frontend (Vercel)

1. Sign in to [vercel.com/dashboard](https://vercel.com/dashboard).
2. **Add New…** → **Project** → import this GitHub repo.
3. In the configuration screen:
   - **Root Directory** → click *Edit* → select `frontend`
   - **Framework Preset** → Vite (auto-detected)
   - Leave Build / Output / Install commands as detected
4. Under **Environment Variables**, add:
   - `VITE_API_URL` → `https://disha-backend.onrender.com`
     (the URL from Step 1, **no trailing slash**, **no `/api/v1`**)
5. Click **Deploy**. Copy the production URL, e.g.
   `https://disha-chatbot.vercel.app`.

### Step 3 — Close the loop

Back in Render → `disha-backend` → **Environment** tab:

- Set `FRONTEND_ORIGIN` to your Vercel URL, e.g. `https://disha-chatbot.vercel.app`
- Save — Render will redeploy automatically.

You're live. Every `git push` to `main` now redeploys both services.

---

## CORS note

The backend middleware allows:

- Every origin in `FRONTEND_ORIGIN` (comma-separated supported)
- `http://localhost:5173`, `http://localhost:5175`, `http://localhost:3000` always
- Any `https://*.vercel.app` (covers Vercel preview deployments)

So preview deployments (branch PRs on Vercel) will just work.

---

## Smoke test after deploy

```bash
BASE=https://disha-chatbot.vercel.app

# 1. Frontend loads
curl -s -o /dev/null -w "%{http_code}\n" $BASE

# 2. Backend reachable through Vercel env → Render
API=https://disha-backend.onrender.com
curl -s $API/api/v1/health
```

Expected: frontend `200`, backend `{"status":"ok",...}`.

---

## Project layout

- `backend/app/api/v1/` — REST routes (chat, session, files, facilities, etc.)
- `backend/app/services/` — LLM, RAG, OCR, maps, prompt builder, session store
- `backend/app/models/schemas.py` — Pydantic schemas (single source of truth)
- `backend/app/data/seed/` — seed KB: FAQ, health tips, crisis helplines
- `frontend/src/components/` — React components
- `frontend/src/views/` — top-level views (Chat, Docs, Tips, Maps, Consent)
- `frontend/src/api/client.ts` — typed REST client
- `frontend/src/state/store.ts` — Zustand store (language, session, messages)

---

## License

Private project for SickleSetu hackathon. Not for redistribution.
