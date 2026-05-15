"""Main entry point for Notification Service."""

from fastapi import FastAPI
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Notification Service",
    description="Multi-channel notification delivery and management",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notification_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port + 4,
        reload=settings.debug,
    )
