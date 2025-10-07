FROM python:3.11-slim

WORKDIR /app

COPY services/transaction_service /app

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
    "8002",
    "--ssl-keyfile",
    "/certs/transaction_service.key",
    "--ssl-certfile",
    "/certs/transaction_service.crt",
    "--ssl-ca-certs",
    "/certs/ca.crt",
    "--ssl-cert-reqs",
    "2"
]
