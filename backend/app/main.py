from fastapi import FastAPI

from app.database import engine


app = FastAPI(
    title="Mini Hiring Pipeline API",
    description="API for managing candidates through a hiring pipeline.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "database": engine.url.get_backend_name(),
    }