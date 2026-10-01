# Testing

Backend tests use pytest and avoid live external services. Current unit coverage validates Haversine distance, booking transition rules, Razorpay HMACs, and the missing-key AI behavior. API OpenAPI smoke checks and Alembic offline SQL generation should also run locally. Run from `backend`: `python -m pytest -q`, `python -m compileall -q app tests`, and `ruff check app tests`. `pytest.ini` adds the backend root to pytest's import path so direct `pytest -q` works on Windows too. Frontend checks: `npm run lint` and `npm run build` from `frontend`.

The local suite still needs PostgreSQL-backed API/ownership integration fixtures and broader Redis invalidation, Celery retry, full Razorpay webhook replay/out-of-order, and mocked Gemini success-path tests. CI starts isolated PostgreSQL and Redis services but the current unit suite does not yet exercise every route against them. Do not infer production acceptance from unit tests alone.
