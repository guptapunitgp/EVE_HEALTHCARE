# EVE Healthcare

EVE is a healthcare diagnostics booking platform with public centre/test discovery, a patient appointment and payment flow, a scoped centre-staff workspace, and platform administration.

## Product areas

- Public centre search by name, city, service, or optional GPS radius; test catalogue with preparation and sample information.
- Firebase Google/email authentication, verified backend exchange, expiring JWT sessions, logout invalidation, and role protected routes.
- Patient dashboard, booking lifecycle, retryable Razorpay checkout, verified payment history, and educational Gemini assistant.
- Admin tools for users, centre catalogue, diagnostic tests, bookings, payment events, outbox notifications, and audit history.
- Centre staff assignment, centre-scoped catalogue pricing/availability, booking management, and activity summary.
- Haversine distance, Redis cache, Redis rate limits, durable notification outbox, Celery worker/Beat, request IDs, readiness checks, Docker Compose, and GitHub Actions.

## Stack and layout

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, Celery, Pydantic 2.
- Frontend: React, Vite, React Router, Axios, Firebase Auth, responsive CSS.
- `backend/app/api`: versioned routes, role and ownership checks.
- `backend/app/models`, `schemas`, `services`, `core`, and `db`: domain data, validation, workflows, configuration, and migrations.
- `frontend/src/pages`: public, patient, staff, admin, and assistant experiences.
- `docs`: architecture, API, database, security, testing, and deployment notes.

## Prerequisites

Python 3.12+, Node.js 22+, PostgreSQL 17, Redis 7. Docker Desktop is optional for local development and required for the Compose instructions below.

## Local development (PowerShell)

1. Copy `backend/.env.example` to `backend/.env`. Set a strong random `JWT_SECRET_KEY`; configure `DATABASE_URL`, Firebase credentials, and `INITIAL_ADMIN_EMAIL`. Keep secrets in the ignored `.env` file. To use Compose only for data services, copy root `.env.example` to `.env` and start Docker Desktop.
2. Start PostgreSQL on port 5433 and Redis on 6379. Or use `docker compose up -d postgres redis` from the repository root.
3. Start the backend:

       cd backend
       py -3.12 -m venv .venv
       .\.venv\Scripts\Activate.ps1
       pip install -r requirements.txt
       alembic upgrade head
       uvicorn app.main:app --reload

   For a first local walkthrough, seed the bundled sample centre/test catalogue after migration:

       python scripts/seed_demo.py --confirm-demo-data

   This inserts only missing sample records, requires `ENVIRONMENT=development`, and leaves existing records untouched.

4. In another terminal, copy `frontend/.env.example` to `frontend/.env.local`, configure the Firebase web app, and run:

       cd frontend
       npm ci
       npm run dev

5. Run the durable mock-notification worker in another backend terminal:

       cd backend
       .\.venv\Scripts\Activate.ps1
       celery -A app.core.celery_app.celery_app worker --beat --loglevel=INFO --pool=solo

API docs: http://localhost:8000/docs. Readiness: http://localhost:8000/api/v1/ready. The frontend dev server is normally at http://localhost:5173.

## First administrator and staff

Set `INITIAL_ADMIN_EMAIL` to the operator-controlled email for the first Firebase account. That exact, Firebase-verified identity receives the administrator role at sign-in; role is never accepted from a browser request. The administrator can assign existing users to diagnostic centres from **Users and Staff**. A user must sign in once before assignment so their account exists. Centre deletion is soft deactivation to preserve booking history.

## Docker Compose

Install and start Docker Desktop, then copy `.env.example` to `.env` and `backend/.env.example` to `backend/.env`. Configure Firebase web settings in the root `.env` before building the frontend. From the repository root:

    docker compose up --build -d
    docker compose exec backend alembic upgrade head
    docker compose ps
    docker compose logs -f backend celery

UI: http://localhost:8080; API docs: http://localhost:8000/docs. PostgreSQL and Redis data use named volumes. `docker compose down` preserves those volumes; `docker compose down -v` deletes them.

For an existing PostgreSQL volume, `POSTGRES_PASSWORD` must match the password that was set when that volume was first initialized; changing the environment variable does not change a stored PostgreSQL role password. `EVE_DATABASE_URL` can point the backend and worker at an existing database credential without resetting its volume. Put it in the ignored root `.env`; for a fresh volume, `POSTGRES_PASSWORD` sets the initial role password. If the existing password is unknown, preserve the old volume and configure a new, separately named volume rather than deleting or resetting existing data.

## Environment variables

See [.env.example](.env.example), [backend/.env.example](backend/.env.example), and [frontend/.env.example](frontend/.env.example). Backend settings include `DATABASE_URL`, `JWT_SECRET_KEY`, token expiry and algorithm, `ENVIRONMENT`, `CORS_ORIGINS`, `ENABLE_DEV_AUTH`, `INITIAL_ADMIN_EMAIL`, Firebase Admin path/project ID, Razorpay test key ID/secret/webhook secret, Gemini API key/model, Redis URL, and Celery broker/result URLs. Frontend settings include `VITE_API_BASE_URL` and Firebase web-app values. Never put service-account or payment secrets in `VITE_` variables.

## Migrations and checks

From `backend`, inspect the configured target before upgrading:

    alembic current
    alembic heads
    alembic upgrade head
    python -m compileall -q app tests
    ruff check app tests
    python -m pytest -q

From `frontend` run `npm run lint` and `npm run build`. Migrations are additive and preserve existing rows. Review the generated changes and back up production before applying them.

## Booking, payments, and notifications

The backend calculates booking prices from the selected centre offering, validates future timezone-aware appointment times, serializes slot creation on the offering row, and records state transitions. Patients can cancel eligible bookings while no payment is unresolved. Confirmed/paid bookings cannot be cancelled without a refund policy.

Razorpay is test-mode only. Order creation uses backend keys; the browser Checkout result is HMAC-verified by the backend, and provider webhooks validate raw-body HMAC, event ID, order ID, amount, and currency. Payment retries preserve attempt history. There is no refund flow or production mode.

To send a correctly signed local webhook for a test order, run from `backend` after configuring `RAZORPAY_WEBHOOK_SECRET`:

    python scripts/simulate_webhook.py --order-id order_... --payment-id pay_local_... --amount-paise 49900 --status captured

Notifications are stored in the database outbox in the same transaction as booking/payment state. Celery Beat retries pending outbox events; current delivery only writes a mock notification to structured logs and does not send email/SMS.

## Educational assistant

`POST /api/v1/ai/education` calls Gemini through its REST `generateContent` API. The backend keeps the API key server-side, limits each account to 12 requests per minute through Redis, caps message size/history, and instructs the model to provide general education only. The UI displays a medical disclaimer. It is not for diagnosis or treatment decisions. If the key is absent, the API reports that the feature is not configured.

## Deployment

No deployment target is configured and nothing has been deployed. Before production, provision managed PostgreSQL and Redis, store credentials in a secret manager, use TLS and exact CORS origins, configure backups and restore drills, review migrations, and validate authentication/payment flows using provider test mode. The current payment integration intentionally rejects live Razorpay mode.

See [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md), [docs/database.md](docs/database.md), [docs/security.md](docs/security.md), [docs/testing.md](docs/testing.md), and [docs/deployment.md](docs/deployment.md).
