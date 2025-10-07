FROM python:3.11-slim

WORKDIR /app

COPY services/auth_service /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" sqlmodel asyncpg python-multipart

CMD ["uvicorn", "presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]
