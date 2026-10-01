# Security

- Firebase ID tokens are verified server-side with revocation checking; local JWT signatures and expiry are validated, then the database supplies the user's role.
- Role assignment is not accepted from the browser. `/auth/dev-promote-admin` was removed. `/auth/dev-login` is disabled unless explicitly enabled in development.
- Booking reads and writes are scoped to the authenticated patient. Booking price comes from the selected offering.
- Payment keys remain server-side. Webhook HMAC uses raw request bytes and constant-time comparison; event IDs are unique.
- CORS is configurable. Set exact origins in production and use TLS.
- `.env`, frontend local env, and Firebase credential directories are ignored. Rotate any credential that has ever been committed or exposed.
- Frontend JWT is stored in sessionStorage, which is accessible to same-origin scripts. Production should add a same-site, secure, HttpOnly cookie/session architecture and a CSP.
- Configure a strong random JWT secret; the development fallback is not suitable for deployment. Do not expose health request bodies or secrets in logs.

The present app is not a certified medical record system. Avoid storing unnecessary sensitive health data and obtain an appropriate privacy/security review before handling regulated production data.
