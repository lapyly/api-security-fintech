FROM python:3.11-slim

WORKDIR /app

COPY services/account_service /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlmodel \
    asyncpg \
    pyjwt \
    cryptography \
    fastapi-limiter \
    redis \
    python-json-logger

CMD [
    "uvicorn",
    "presentation.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8001",
    "--ssl-keyfile",
    "/certs/account_service.key",
    "--ssl-certfile",
    "/certs/account_service.crt",
    "--ssl-ca-certs",
    "/certs/ca.crt",
    "--ssl-cert-reqs",
    "2"
]
