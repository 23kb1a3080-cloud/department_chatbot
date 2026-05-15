"""Main entry point for Document Processing Service."""

from fastapi import FastAPI
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Document Processing Service",
    description="Document ingestion, processing, and knowledge base management",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port + 3,
        reload=settings.debug,
    )
