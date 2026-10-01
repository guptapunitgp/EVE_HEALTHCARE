# Database

PostgreSQL is accessed with SQLAlchemy 2 and managed by Alembic. Main tables are `users`, `diagnostic_centres`, `diagnostic_tests`, `centre_tests`, `centre_staff`, `bookings`, `booking_events`, `payments`, `webhook_events`, and `notification_outbox`. Payments are one-to-many per booking to preserve retry history. Foreign keys restrict deleting a patient or booking with dependent records; centre/test offering references cascade. Prefer soft-deactivation for catalogue entries that have bookings.

Use `cd backend; alembic current; alembic heads; alembic upgrade head` after selecting the correct `DATABASE_URL`. Existing migration history contains no-op duplicate revisions (`ccec565bda36`, `0a2075552a45`); they are retained so already-recorded installations keep a valid linear revision chain. Inspect generated SQL and take backups before production upgrades.

New schema revisions add deactivation, centre contact/hours/services, test category/sample/report details, staff assignment, payment retries/currency, booking events, and outbox records. Schema changes should remain additive and reversible; never recreate existing tables in place.
