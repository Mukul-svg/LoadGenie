"""
Health check and utility routes
"""

import time
from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", 
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
