"""Main entry point for Authentication Service."""

from fastapi import FastAPI
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Authentication Service",
    description="User authentication, authorization, and session management",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
