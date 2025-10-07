FROM python:3.11-slim

WORKDIR /app

COPY services/audit_service /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
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
    "8003",
    "--ssl-keyfile",
    "/certs/audit_service.key",
    "--ssl-certfile",
    "/certs/audit_service.crt",
    "--ssl-ca-certs",
    "/certs/ca.crt",
    "--ssl-cert-reqs",
    "2"
]
