FROM python:3.11-slim

WORKDIR /app

COPY services/monitoring_service /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]"

CMD ["uvicorn", "presentation.main:app", "--host", "0.0.0.0", "--port", "8004"]
