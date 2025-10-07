FROM python:3.11-slim

WORKDIR /app

COPY services/monitoring_service /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pyjwt \
    cryptography \
    fastapi-limiter \
    redis \
    python-json-logger \
    prometheus-fastapi-instrumentator

CMD [
    "uvicorn",
    "presentation.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8004",
    "--ssl-keyfile",
    "/certs/monitoring_service.key",
    "--ssl-certfile",
    "/certs/monitoring_service.crt",
    "--ssl-ca-certs",
    "/certs/ca.crt",
    "--ssl-cert-reqs",
    "2"
]
