from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router, linear_poll_worker
from app.api.discovery_routes import router as discovery_router
from app.api.hardware_companion_routes import router as hardware_companion_router
from app.api.organization_os_routes import router as organization_os_router
from app.api.simulation_world_routes import router as simulation_world_router
from app.api.innovation_lab_routes import router as innovation_lab_router
from app.api.executive_board_routes import router as executive_board_router
from app.api.business_operator_routes import router as business_operator_router
from app.api.saas_builder_routes import router as saas_builder_router
from app.api.universal_operator_routes import router as universal_operator_router
from app.api.life_os_routes import router as life_os_router
from app.api.avatar_routes import router as avatar_router
from app.api.training_lab_routes import router as training_lab_router
from app.api.departments_routes import router as departments_router
from app.api.research_routes import router as research_router
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
app.include_router(hardware_companion_router, prefix="/api")
app.include_router(organization_os_router, prefix="/api")
app.include_router(simulation_world_router, prefix="/api")
app.include_router(innovation_lab_router, prefix="/api")
app.include_router(executive_board_router, prefix="/api")
app.include_router(business_operator_router, prefix="/api")
app.include_router(saas_builder_router, prefix="/api")
app.include_router(universal_operator_router, prefix="/api")
app.include_router(life_os_router, prefix="/api")
app.include_router(avatar_router, prefix="/api")
app.include_router(training_lab_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(feature_router, prefix="/api")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
