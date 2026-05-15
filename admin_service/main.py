"""Main entry point for Admin Service."""

from fastapi import FastAPI
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Admin Service",
    description="Administrative interface and system management",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port + 5,
        reload=settings.debug,
    )
