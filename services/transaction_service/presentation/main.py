from fastapi import FastAPI

from .api import router


app = FastAPI(title="Transaction Service", version="0.1.0")
app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

