FROM python:3.11-slim

WORKDIR /app

COPY services/auth_service /app

# Include shared utilities used by services (e.g., services.common)
COPY services/common /app/services/common

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlmodel \
    asyncpg \
    python-multipart \
    pyjwt \
    cryptography \
    fastapi-limiter==0.1.6 \
    redis==5.0.3 \
    python-json-logger \
    prometheus-fastapi-instrumentator

CMD ["uvicorn","presentation.main:app","--host","0.0.0.0","--port","8000","--ssl-keyfile","/certs/auth_service.key","--ssl-certfile","/certs/auth_service.crt","--ssl-ca-certs","/certs/ca.crt","--ssl-cert-reqs","2"]
