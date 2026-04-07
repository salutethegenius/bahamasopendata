# Security operations — Bahamas Open Data

## Ingestion API keys (R02)

Long-lived `X-API-Key` values can run ingestion and document workflows with the same API surface as admin JWTs for those routes. Treat keys like production secrets: store in a secrets manager, rotate on schedule, revoke when staff change roles, and never commit raw keys. Prefer separate keys per environment. Future hardening: scoped keys (read-only vs publish).

## PostgreSQL RLS (R11)

Authorization is enforced in FastAPI, not row-level security in Postgres. RLS remains optional defense-in-depth if the threat model warrants it (e.g. shared DB analyst access). Enabling RLS would require policies per table and application role wiring.

## Automation / CLI auth

Login responses no longer return a JWT in JSON; the access token is an **httpOnly** cookie. Scripts should use **ingestion API keys** (`X-API-Key`) or a cookie-aware HTTP client, not `access_token` from a JSON body.

## Production checklist

- `DEBUG=false`, `SQLALCHEMY_ECHO=false`
- `ENABLE_OPENAPI=false` (disable `/docs` / OpenAPI)
- `ALLOW_INITIAL_SUPERUSER_BOOTSTRAP=false` after the first superuser exists; unset `INITIAL_SUPERUSER_*`
- `ENABLE_METADATA_CREATE_ALL=false` when using Alembic only; run `alembic upgrade head`
- `REDIS_URL` set when running multiple API workers or instances (shared rate limits)
- `FINGERPRINT_PEPPER` set to a long random value (poll vote privacy)
- `COOKIE_SECURE=true` behind HTTPS
- `TRUSTED_PROXY_COUNT` matches your reverse-proxy chain
