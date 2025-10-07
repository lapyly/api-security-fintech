from fastapi import Depends, FastAPI

from ..infrastructure.rate_limiting import register_rate_limiter
from .api import router
from .dependencies import get_current_principal
from .middleware import setup_middleware
from .metrics import setup_metrics

app = FastAPI(title="Audit Service", version="0.2.0")
setup_middleware(app)
setup_metrics(app)
register_rate_limiter(app)
app.include_router(router)


@app.get("/health", tags=["health"], dependencies=[Depends(get_current_principal)])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

