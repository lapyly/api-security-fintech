from fastapi import FastAPI

app = FastAPI(title="Monitoring Service", version="0.1.0")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

