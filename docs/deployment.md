# Free-tier demo deployment

This configuration is for a public demo only. Free hosting does not provide a production service level for healthcare workloads. Do not use it for real patient records or real payments. Razorpay is restricted to test mode, notifications are mock-only, and the application still needs an independent privacy/security review.

## Services

- Frontend: Vercel, project root `frontend`, build `npm run build`, output `dist`.
- API: existing Render web service, Dockerfile `backend/Dockerfile`, health check `/api/v1/ready`.
- Database: existing Neon PostgreSQL project. Use its pooled URL for runtime and its direct (non-pooler) URL for manual Alembic migrations.
- Redis: existing Upstash Redis TLS URL (`rediss://`). Do not reuse any credential previously exposed in chat; rotate it in Upstash, then replace it in Render's environment.

The Render free web service sleeps after 15 minutes idle and can take about a minute to wake. Neon and Upstash also enforce free usage limits. Render does not offer a free continuously running Celery worker, so booking notifications remain in the durable outbox until a worker runs. The app's health endpoint reports Redis availability; `/api/v1/ready` reports database and Redis readiness.

## Render environment

In the existing Render service, set these values in **Environment**. Keep credentials only in Render's secret environment settings; do not paste them into this repository or chat.

| Variable | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `ENABLE_DEV_AUTH` | `false` |
| `DATABASE_URL` | Neon pooled PostgreSQL URL, with the SQLAlchemy `postgresql+psycopg://` driver prefix |
| `MIGRATION_DATABASE_URL` | Neon direct (non-pooler) URL, same driver prefix; needed only for migrations |
| `REDIS_URL` | Rotated Upstash TLS URL (`rediss://...`) |
| `CELERY_BROKER_URL` | Omit to use `REDIS_URL`, or set to the same Upstash TLS URL |
| `CELERY_RESULT_BACKEND` | Omit to use `REDIS_URL`, or set to the same Upstash TLS URL |
| `JWT_SECRET_KEY` | A unique random value of at least 32 characters |
| `CORS_ORIGINS` | `https://eve-healthcare-nu.vercel.app` |
| `FIREBASE_PROJECT_ID` | Firebase project ID used by the frontend |
| `FIREBASE_CREDENTIALS_JSON` | Firebase Admin service account JSON stored as a Render secret; alternatively configure `FIREBASE_CREDENTIALS_PATH` using a secret file |
| `RAZORPAY_MODE` | `test` |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Test credentials from Razorpay, if exercising checkout |
| `GEMINI_API_KEY` | Optional; needed for the educational assistant |

Set the service health check path to `/api/v1/ready`. Do not set the API base URL to include `/api/v1`; the frontend adds that prefix itself. Do not reset the Neon database. It is already migrated according to the project handoff. For a future planned migration, run `alembic upgrade head` from `backend` with `MIGRATION_DATABASE_URL` pointed at the direct Neon URL, after taking a backup/branch.

## Vercel project

Configure the existing Vercel project with:

- Root directory: `frontend`
- Install command: `npm install`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable `VITE_API_BASE_URL`: `https://eve-healthcare-iqyd.onrender.com` (no `/api/v1` suffix)
- Set the six public `VITE_FIREBASE_*` web-app values from Firebase; these are browser config, not Admin credentials.

The checked-in `frontend/vercel.json` rewrites direct React routes to `index.html`, so nested routes work after refresh. In Firebase Authentication, add `eve-healthcare-nu.vercel.app` to authorized domains and enable the Google provider. In Render, keep `CORS_ORIGINS` limited to the exact deployed frontend origin.

## Checks after deployment

After saving environment changes and deploying, verify:

1. `https://eve-healthcare-iqyd.onrender.com/` returns the API root response.
2. `https://eve-healthcare-iqyd.onrender.com/api/v1/health` reports Redis true (or `degraded` if unavailable).
3. `https://eve-healthcare-iqyd.onrender.com/api/v1/ready` returns 200 with database and Redis true.
4. `https://eve-healthcare-iqyd.onrender.com/api/v1/centres?limit=3` returns a page.
5. `https://eve-healthcare-nu.vercel.app/` loads, and a nested route survives refresh.
6. Firebase sign-in works after the authorized domain and backend Admin credential are configured.

An HTTP 200 from Render does not establish production readiness. Render Free is explicitly intended for testing/hobby use, Vercel Hobby is limited to personal/non-commercial use, and these service tiers do not supply the uptime, backups, operational coverage, or healthcare compliance needed for real patient use.
