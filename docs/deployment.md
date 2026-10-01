# Deployment

No deployment target is selected or configured. Build the backend from `backend/Dockerfile` and static frontend from `frontend/Dockerfile`; Compose is for local development, not a production secret manager.

Provision PostgreSQL and Redis with backups, configure the application environment and exact CORS origins, set TLS at the ingress, store Firebase/Razorpay/Gemini/JWT credentials in the host secret manager, and run `alembic upgrade head` as a controlled release step. Monitor `/api/v1/health` and `/api/v1/ready`, request IDs and worker logs. Test database restore and Razorpay test webhooks before any production payment configuration.

CI at `.github/workflows/ci.yml` runs Python checks/tests, Alembic head inspection, and frontend lint/build. Pin and review GitHub Actions and dependency upgrades as part of routine maintenance. No publish or deployment has been performed.
