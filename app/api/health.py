"""
Health check endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import get_db
from app.schemas.graph import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check the health status of the service.
    
    Verifies that the API is running and can connect to the database.
    
    **Returns:**
    - **status**: Service status (healthy/unhealthy)
    - **database**: Database connection status
    - **timestamp**: Current server timestamp
    
    **Status Codes:**
    - **200**: Service is healthy
    - **503**: Service is unhealthy
    """
    try:
        # Test database connectivity
        await db.execute(text("SELECT 1"))
        
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
