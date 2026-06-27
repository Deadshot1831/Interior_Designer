# RoomAI (Lite — Phase 1)

Upload a photo of a room and get an AI-generated interior design report:
detected room type, recommended palette, furniture suggestions, and layout
advice. Phase 1 is analysis-only (no image regeneration).

**Design principle:** be conservative. The vision prompt instructs Claude to
only describe what's actually visible in the photo and to never suggest
placements that block a real door, window, or walkway — directly addressing the
#1 complaint about existing tools (misidentifying elements, ignoring geometry).

## Stack

- **Backend:** Python 3.11+ (developed on 3.12), FastAPI, Pydantic v2,
  SQLAlchemy + Alembic, JWT auth. Claude multimodal API for vision + reasoning.
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS.
- **DB:** SQLite for local dev (default); swap `DATABASE_URL` to Postgres with no
  code changes.
- **Storage:** local filesystem (`/storage/uploads`), behind a `Storage`
  protocol so S3/R2 can be added later.

```
roomai/
├── backend/    # FastAPI app, models, services, tests
└── frontend/   # Next.js app
```

## Prerequisites

- Python 3.11 or 3.12 (3.14 not recommended — some deps lack wheels)
- Node.js 18+
- An Anthropic API key (for live room analysis)
- [`uv`](https://github.com/astral-sh/uv) recommended (or plain `venv` + `pip`)

## Backend setup

```bash
cd backend

# 1. Create a virtualenv (Python 3.12) and install deps
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
# (or: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt)

# 2. Configure environment
cp .env.example .env
#   - set ANTHROPIC_API_KEY=sk-ant-...   (required for analysis)
#   - set JWT_SECRET to a long random string
#   - DATABASE_URL defaults to sqlite:///./roomai.db

# 3. Create the database schema
.venv/bin/alembic upgrade head

# 4. Run the API (http://localhost:8000, docs at /docs)
.venv/bin/uvicorn app.main:app --reload
```

### Switching to Postgres

Set `DATABASE_URL=postgresql://user:pass@localhost:5432/roomai` in `.env`, then
`alembic upgrade head`. No model or query changes needed.

## Frontend setup

```bash
cd frontend
npm install

cp .env.local.example .env.local
#   - NEXT_PUBLIC_API_BASE=http://localhost:8000  (default)

npm run dev   # http://localhost:3000
```

Open http://localhost:3000, sign up (you get 3 free credits), upload a room
photo, pick a style, and view the generated report.

## Environment variables

### Backend (`backend/.env`)
| Var | Purpose | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key for vision analysis | _(required)_ |
| `ANTHROPIC_MODEL` | Model id used for analysis | `claude-opus-4-8` |
| `DATABASE_URL` | DB connection string | `sqlite:///./roomai.db` |
| `JWT_SECRET` | Secret for signing JWTs | _(set this!)_ |
| `STORAGE_PATH` | Where uploads are stored | `./storage/uploads` |
| `ENVIRONMENT` | Environment label | `development` |

### Frontend (`frontend/.env.local`)
| Var | Purpose | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE` | Backend base URL | `http://localhost:8000` |

## Running tests

```bash
cd backend
.venv/bin/python -m pytest -q
```

Tests use an isolated in-memory SQLite DB and a fully mocked Anthropic client,
so they need **no** API key. Coverage includes:

- Auth: signup, login, duplicate email, JWT-protected routes
- Upload validation: type, size, min-dimension checks
- Vision service: JSON parse, schema validation, **retry-once-then-succeed**,
  and **fail-after-retry**
- Credits: deduction on success, and the critical **no-deduction-on-failure**
  path
- End-to-end: signup → upload → design → fetch, asserting credit drops exactly
  once

```bash
cd frontend
npm run build   # type-checks + lints the whole app
```

## API summary

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/auth/signup` | `{email, password}` → `{access_token, user}` |
| `POST` | `/auth/login` | `{email, password}` → `{access_token, user}` |
| `GET` | `/auth/me` | current user (Bearer token) |
| `POST` | `/rooms` | multipart `image`; validates type/size/dimensions |
| `POST` | `/rooms/{id}/designs` | `{style}`; 402 `out_of_credits` when exhausted |
| `GET` | `/designs/{id}` | full design report |
| `GET` | `/users/me/designs` | dashboard list |

Styles (fixed enum): `scandinavian`, `minimalist`, `industrial`, `bohemian`,
`modern_indian`, `traditional_indian`, `mid_century`, `coastal`.

## Out of scope for Phase 1

Payments, real furniture-catalog matching, image-to-image regeneration,
before/after slider, AR preview, and background job queues. Extension points are
marked with `# TODO(phase2):` / `# TODO(phase3):` in the code (e.g. S3 storage in
`backend/app/services/storage.py`, Stripe checkout in the dashboard upgrade
prompt).

## Notes

- **Live vision verification:** the vision service is built and unit-tested
  against a mocked Claude client. To verify against the real API (spec build
  step 5), set `ANTHROPIC_API_KEY` and create a design through the UI or call
  `POST /rooms/{id}/designs`. Iterate on the prompt in
  `backend/app/services/vision.py` if output quality needs tuning.
- Uploaded images are served by the backend at `/storage/...` and rendered by
  the frontend via `resolveImageUrl()`.
```
