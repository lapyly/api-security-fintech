FROM python:3.11-slim

WORKDIR /app

# Copiar solo el servicio y la carpeta común
COPY services/auth_service /app/services/auth_service
COPY services/common /app/services/common

# Instalar dependencias
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

# Registrar el path base
ENV PYTHONPATH=/app

# Ejecutar el servidor
CMD ["uvicorn", "services.auth_service.presentation.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/certs/auth_service.key", "--ssl-certfile", "/certs/auth_service.crt", "--ssl-ca-certs", "/certs/ca.crt", "--ssl-cert-reqs", "2"]
