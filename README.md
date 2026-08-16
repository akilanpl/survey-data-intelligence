# Intelligent Survey Data Validation Platform

Hackathon build frozen through **Phase 11**. Deterministic survey-data intelligence for supervisor review. Sample extracts are **synthetic/demo data**, not live government survey microdata.

```
CSV or eSIGMA JSON
        ↓
   Standardizer
        ↓
      Parquet
        ↓
      SIRL
        ↓
Rules + Statistics + Isolation Forest
        ↓
   Evidence fusion → risk score
        ↓
Optional AI explanation (never the source of truth)
        ↓
Supervisor dashboard + investigation + audit
```

AI must not change risk, severity, or agreement. Live eSIGMA is only real if `ESIGMA_BASE_URL` is configured **and** a probe succeeds.

Stack: FastAPI, SQLite, Parquet, Next.js. No Redis, Kafka, Celery, Kubernetes, or vector databases.

## Environment

Copy `.env.example` to `.env` at the **repository root**. `.env` is gitignored. Do not put secrets in frontend code.

Required for any shared/demo host:

- `JWT_SECRET` — replace the placeholder; do not ship the example value
- `AUTH_ADMIN_PASSWORD` / `AUTH_SUPERVISOR_PASSWORD` — change default hackathon passwords
- `AUTH_COOKIE_SECURE=true` when serving over HTTPS
- Persistent disk for `data/app.db` and `data/processed/` (SQLite + Parquet). An ephemeral filesystem will lose batches after restart.

Default login accounts are **hackathon/demo only**:

- `admin` / `admin` — `SURVEY_ADMIN`
- `supervisor` / `supervisor` — `FIELD_SUPERVISOR`

`AUTH_DEMO_MODE=true` also seeds the optional demo username from `SUPERVISOR_USER`.

Leave `AI_*` and `ESIGMA_*` empty to run fully deterministic. `ESIGMA_MOCK_MODE=true` uses the bundled fixture.

Frontend API:

- Same-origin (recommended): leave `NEXT_PUBLIC_API_BASE_URL` empty. Next.js rewrites `/api/*` to `BACKEND_URL` (default `http://127.0.0.1:8000`).
- Split origin: set `NEXT_PUBLIC_API_BASE_URL` to the API origin and configure CORS. Cookies need a shared site or HTTPS `Secure` + appropriate `SameSite`.

## Backend

Python 3.11+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health: `GET /api/health` → `{"status":"ok"}`.

Tests:

```bash
cd backend
.venv/bin/pytest -q
```

## Frontend

Node.js 20+.

```bash
cd frontend
npm install
npm run build
npm run start -- --port 3000
```

Open http://localhost:3000. Sign in, ingest a sample CSV from `data/samples/`, then **Run validation** on the batch page (ingestion does not auto-run the full pipeline).

## Persistence (deployment)

This app is process + local files, not a hosted blueprint. Keep:

- SQLite: `DATABASE_URL` / `data/app.db`
- Parquet: `DATA_DIR/processed/`

If those paths are not on a persistent volume, data will disappear on remount.

## Security notes

- Secrets belong in environment variables, never in the Next.js bundle
- Session cookie: httpOnly, SameSite=lax; set `AUTH_COOKIE_SECURE=true` on HTTPS
- Placeholder JWT/demo passwords are not production identity
- Do not claim live eSIGMA or live AI unless those env vars are set and health/probe succeed
