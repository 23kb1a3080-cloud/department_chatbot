"""Main entry point for RAG Pipeline Service."""

from fastapi import FastAPI
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="RAG Pipeline Service",
    description="Retrieval-Augmented Generation for intelligent responses",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port + 2,
        reload=settings.debug,
    )
