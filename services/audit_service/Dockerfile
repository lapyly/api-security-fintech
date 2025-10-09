FROM python:3.11-slim

WORKDIR /app

COPY services/audit_service /app/services/audit_service

# Include shared utilities used by services (e.g., services.common)
COPY services/common /app/services/common

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pyjwt \
    cryptography \
    fastapi-limiter==0.1.6 \
    redis==5.0.3 \
    python-json-logger \
    prometheus-fastapi-instrumentator

ENV PYTHONPATH=/app

CMD ["uvicorn","services.audit_service.presentation.main:app","--host","0.0.0.0","--port","8003","--ssl-keyfile","/certs/audit_service.key","--ssl-certfile","/certs/audit_service.crt","--ssl-ca-certs","/certs/ca.crt","--ssl-cert-reqs","2"]
