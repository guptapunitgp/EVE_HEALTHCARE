# API reference

OpenAPI is generated at `/docs` and `/openapi.json` when the backend is running.

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/health` | public | Liveness and Redis indicator |
| GET | `/api/v1/ready` | public | Database and Redis readiness |
| POST | `/api/v1/auth/firebase` | public | Firebase ID token exchange |
| GET | `/api/v1/auth/me` | bearer | Current user profile |
| PATCH | `/api/v1/auth/me` | bearer | Update profile name |
| POST | `/api/v1/auth/logout` | bearer | Revoke current JWT through Redis |
| GET | `/api/v1/centres` | public | Active centre catalogue, text/city/service filters, offset pagination |
| GET | `/api/v1/centres/nearby` | public | Haversine search by coordinates/radius, offset pagination |
| GET | `/api/v1/centres/{id}` | public | Centre detail |
| GET | `/api/v1/tests` | public | Active test catalogue with text/category filters and pagination |
| GET | `/api/v1/centre-tests` | public | Available offerings with centre/test filters and pagination |
| POST/DELETE | `/api/v1/centres/{id}/staff` | admin | Assign/remove centre staff |
| GET | `/api/v1/staff/overview` | staff/admin | Centre scoped summary |
| GET | `/api/v1/staff/bookings` | staff/admin | Centre scoped bookings |
| GET | `/api/v1/staff/offerings` | staff/admin | Centre scoped offerings, including unavailable entries |
| POST | `/api/v1/bookings` | bearer patient | Request appointment |
| GET | `/api/v1/bookings` | bearer patient | Patient's own bookings |
| GET/PATCH | `/api/v1/bookings/{id}` | bearer owner | Read/change eligible booking |
| PATCH | `/api/v1/bookings/{id}/cancel` | bearer owner | Cancel eligible unpaid/failed booking |
| POST | `/api/v1/payments/` | bearer owner | Create or resume a Razorpay order |
| POST | `/api/v1/payments/verify` | bearer owner | Verify Checkout HMAC and confirm payment |
| GET | `/api/v1/payments/` | bearer owner | Payment attempts for the current user |
| POST | `/api/v1/payments/webhook/` | signed provider | Verify Razorpay event HMAC/entity and process idempotently |
| POST | `/api/v1/ai/education` | bearer | Rate-limited Gemini educational response |
| GET | `/api/v1/admin/overview` | admin | Platform counters/status summary |
| GET | `/api/v1/admin/users`, `/centres`, `/tests`, `/bookings` | admin | Paginated management views |
| GET | `/api/v1/admin/audit/booking-events` | admin | Booking transition log |

Admin mutation routes create/update centres, tests, users' active status, and offerings; catalogue deactivation is used instead of destructive deletes. Admin and staff completion actions use centralized booking transitions. Always keep role, patient ID, payment status, provider signature, and price decisions server-side.
