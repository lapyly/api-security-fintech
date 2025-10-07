# api-security-fintech

This Proof of Concept (PoC) demonstrates an end-to-end API security program applied to a fintech transactional landscape. The repository contains multiple FastAPI microservices hardened with role-based access control, rate limiting, observability, and automated testing to illustrate how security and compliance controls can be codified.

## Repository layout

| Path | Description |
| --- | --- |
| `services/` | Source code for the account, transaction, authentication, audit, and monitoring services. Each service exposes FastAPI endpoints with OAuth2 security metadata and OpenAPI contracts. |
| `tests/` | Pytest test suites (unit, integration, security) and a Postman collection with Newman runner for API lifecycle validation. |
| `scripts/` | Utility scripts such as `generate_openapi.py` for regenerating OpenAPI specifications. |
| `logging/`, `monitoring/` | Supporting configuration for observability tooling. |

## Prerequisites

* Python 3.11+
* Node.js 18+ (for running Newman)
* Docker and Docker Compose (for local orchestration and ephemeral test dependencies)
* OpenSSL (for handling the bundled certificates in `certs/`)

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

Node dependencies for Newman can be installed globally or run ad-hoc with `npx`:

```bash
npm install -g newman@5
```

## Environment variables

Each service supports environment-based configuration. Key variables include:

| Variable | Purpose | Default |
| --- | --- | --- |
| `TRANSACTION_DATABASE_URL` | Async SQLAlchemy URL for the transaction service database. | `postgresql+asyncpg://postgres:postgres@db:5432/transactions` |
| `TRANSACTION_DATABASE_SSLMODE` | Controls TLS requirements when connecting to Postgres (`require`/`disable`). | `require` |
| `ACCOUNT_DATABASE_URL` | SQLAlchemy URL for the account service database. | `postgresql+asyncpg://postgres:postgres@db:5432/accounts` |
| `AUTH_TOKEN_URL` / `AUTH_AUTHORIZE_URL` | OAuth2 endpoints used by service documentation. | `https://auth.local/auth/token`, `https://auth.local/oauth/authorize` |
| `DOCS_OAUTH_CLIENT_ID` | Default OAuth client shown in Swagger UI. | `web-portal` |
| `AUTH_PUBLIC_KEY_PATH` | Filesystem path to the RSA public key used for JWT validation. | `/certs/auth_service.crt` |
| `REDIS_URL` | Redis connection string for rate limiting. | `redis://redis:6379/0` |

Services load additional configuration from their respective infrastructure modules; consult `services/*/presentation/dependencies.py` for further details.

## Running the services with Docker Compose

```bash
docker compose up --build
```

The default compose file starts PostgreSQL, Redis, and the FastAPI services. Swagger UI is exposed on the following ports:

| Service | Port |
| --- | --- |
| Account Service | `http://localhost:8002/docs` |
| Transaction Service | `http://localhost:8003/docs` |
| Auth Service | `http://localhost:8001/docs` |
| Audit Service | `http://localhost:8004/docs` |
| Monitoring Service | `http://localhost:8005/docs` |

OAuth2 client credentials can be exercised directly from the interactive documentation using the configured OAuth flows.

## Testing

### Pytest

Run the entire suite (unit, security, and integration) with coverage reporting:

```bash
pytest
```

To execute only fast unit tests:

```bash
pytest -m unit
```

Integration tests spin up ephemeral PostgreSQL containers via `testcontainers`. Ensure Docker is available and, if using TLS-restricted environments, set `TRANSACTION_DATABASE_SSLMODE=disable`.

### Postman & Newman

The Postman collection at `tests/postman/collection.json` exercises authentication, account lifecycle management, and transaction flows. Execute it via Newman:

```bash
./tests/postman/run_newman.sh \
  AUTH_BASE_URL=http://localhost:8001 \
  ACCOUNT_BASE_URL=http://localhost:8002 \
  TRANSACTION_BASE_URL=http://localhost:8003
```

### Coverage target

Continuous integration enforces a minimum combined test coverage of **90%** using `pytest-cov`. Review `.github/workflows/ci.yml` for details.

## Generating OpenAPI specifications

Regenerate the committed OpenAPI contracts after modifying service routes:

```bash
python scripts/generate_openapi.py
```

Specs are stored alongside each service (for example `services/transaction_service/openapi.yaml`). They are referenced by documentation portals and downstream governance tooling.

## Compliance control matrix

| Framework / Control | Implementation artifact(s) | Notes |
| --- | --- | --- |
| OWASP API Security A01 – Broken Object Level Authorization | `services/transaction_service/presentation/dependencies.py`, `tests/security/test_auth_dependencies.py` | Scope and role dependencies enforce object-level access with dedicated security tests. |
| OWASP API Security A05 – Broken Function Level Authorization | `services/account_service/presentation/api.py`, `services/auth_service/presentation/api.py` | Route dependencies require explicit scopes per method to prevent vertical privilege escalation. |
| PCI DSS 4.0 – Requirement 7 (Access Control) | OAuth2 flows defined in `services/*/openapi.yaml`, coverage in Newman tests | OAuth scopes align with PCI role separation; Postman scripts validate lifecycle controls. |
| PCI DSS 4.0 – Requirement 10 (Logging) | `services/audit_service` domain & API, `services/monitoring_service/presentation/api.py` | Audit service captures immutable events with compliance tags, monitoring service logs alert metadata. |
| ISO/IEC 27001:2022 Annex A.8 (Access Control) | `services/auth_service/presentation/main.py`, `services/common/docs.py` | Centralized identity provider with documented OAuth2 flows and secure documentation configuration. |
| ISO/IEC 27001:2022 Annex A.12 (Operations Security) | `tests/integration/test_transaction_repository.py`, Docker Compose stack | Infrastructure-as-code and integration tests validate secure operations with ephemeral databases. |
| NIST SP 800-53 Rev.5 AC-2 (Account Management) | Account service schemas and routes, `tests/postman/collection.json` | Account lifecycle endpoints enforce structured account creation/update and automated validation. |
| NIST SP 800-53 Rev.5 AU-6 (Audit Review) | `services/audit_service/openapi.yaml`, `tests/security/test_auth_dependencies.py` | Security tokens and audit retrieval endpoints support review and correlation activities. |

## Additional resources

* Certificates for local development are provided in `certs/`.
* Rate limiting helpers are implemented with Redis in `services/*/infrastructure/rate_limiting.py`.
* Metrics and middleware setup for each service reside in `services/*/presentation/metrics.py` and `services/*/presentation/middleware.py`.

