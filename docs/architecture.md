# Architecture

The browser app calls the versioned FastAPI routes under `/api/v1`. Firebase Google sign-in provides an ID token; the API verifies it with Firebase Admin and issues an application JWT. Authenticated API dependencies resolve that JWT to a local user before private booking access. Public catalogue reads do not require an account.

SQLAlchemy models map to PostgreSQL through Alembic. Centre list responses use fastapi-cache backed by Redis. Booking and payment transactions write durable notification outbox entries; Celery Beat dispatches pending records to a mock log delivery task. Booking state changes are stored in `booking_events`. Centre staff assignments scope staff operations through `centre_staff`.

Razorpay order creation and checkout use backend credentials, and checkout/webhook results are HMAC-verified. Webhooks parse Razorpay payment entities and verify order ID, amount, and currency before changing payment or booking state. Gemini's REST `generateContent` endpoint provides general education with a Redis per-user rate limit and the API key retained on the backend.

The frontend portal supports city search and optional browser geolocation. Browser location is never required for catalogue browsing. The API computes nearby distance with Haversine.

Current limitations: provider email/SMS delivery, refunds, live Razorpay mode, downloadable lab reports, centre ratings/reviews, and recurring availability schedules are not implemented. Appointment contention uses a single exact timestamp per offering as its slot key; centres needing multiple capacity or duration rules should adopt explicit slot records. JWTs are held in browser sessionStorage; a secure HttpOnly cookie session requires a different frontend/backend session contract.
