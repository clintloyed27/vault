import os
import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.storage import get_storage_service

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Liveness probe returning server status and metadata."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/readiness", status_code=status.HTTP_200_OK)
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe validating database connectivity and storage volume writability.
    Crucial for container orchestration, health monitoring, and zero-downtime deployments.
    """
    health_status = {
        "database": "unknown",
        "storage": "unknown",
        "overall": "unhealthy",
    }
    
    # 1. Test database query
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"

    # 2. Test storage read/write
    try:
        storage = get_storage_service()
        probe_user = "__health_probe__"
        probe_file = f"probe_{uuid.uuid4().hex[:8]}.tmp"
        storage.save_file(probe_user, probe_file, b"OK")
        if storage.file_exists(probe_user, probe_file):
            storage.delete_file(probe_user, probe_file)
            health_status["storage"] = "writable"
        else:
            health_status["storage"] = "write_verification_failed"
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"

    is_ready = (
        health_status["database"] == "connected"
        and health_status["storage"] == "writable"
    )
    health_status["overall"] = "ready" if is_ready else "not_ready"

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=health_status)
