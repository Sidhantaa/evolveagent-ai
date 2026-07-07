from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router, linear_poll_worker
from app.api.discovery_routes import router as discovery_router
from app.api.feature_routes import router as feature_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await linear_poll_worker.start()
    yield
    await linear_poll_worker.stop()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.app_name}


app.include_router(router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(feature_router, prefix="/api")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
