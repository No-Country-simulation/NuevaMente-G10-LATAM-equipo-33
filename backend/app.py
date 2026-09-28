from fastapi import FastAPI

from core.config import settings
from api.adaptation import router as adaptation_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.get(f"{settings.api_prefix}/health")
def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


app.include_router(
    adaptation_router,
    prefix=settings.api_prefix,
)