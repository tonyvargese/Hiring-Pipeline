from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.api.candidates import router as candidates_router
from app.database import Base, engine
from app.api.pipeline import router as pipeline_router
from app.api.search import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Mini Hiring Pipeline API",
    description="API for managing candidates through a hiring pipeline.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(candidates_router)
app.include_router(pipeline_router)
app.include_router(search_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "database": engine.url.get_backend_name(),
    }