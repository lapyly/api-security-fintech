from fastapi import Depends, FastAPI

from ..infrastructure.rate_limiting import register_rate_limiter
from .dependencies import get_current_principal
from .middleware import setup_middleware

app = FastAPI(title="Monitoring Service", version="0.2.0")
setup_middleware(app)
register_rate_limiter(app)


@app.get("/health", tags=["health"], dependencies=[Depends(get_current_principal)])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

