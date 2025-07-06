"""
FastAPI application factory and main application
"""

import time
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.models.schemas import ErrorResponse
from app.services.ai_service import AIServiceError
from app.services.k6_runner import K6RunnerError
from app.api.script_routes import router as script_router
from app.api.health_routes import router as health_router
from app.api.test_routes import router as test_router

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(AIServiceError)
    async def ai_service_exception_handler(request: Request, exc: AIServiceError):
        """Handle AI service specific errors"""
        logger.error(f"AI Service Error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="AI service error",
                detail=str(exc),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ).dict()
        )

    @app.exception_handler(K6RunnerError)
    async def k6_runner_exception_handler(request: Request, exc: K6RunnerError):
        """Handle K6 runner specific errors"""
        logger.error(f"K6 Runner Error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="K6 runner error",
                detail=str(exc),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ).dict()
        )

    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request: Request, exc: ValueError):
        """Handle validation errors"""
        logger.error(f"Validation Error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="Validation error",
                detail=str(exc),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ).dict()
        )
    
    # Include routers
    app.include_router(health_router, tags=["Health"])
    app.include_router(script_router, tags=["Script Generation"])
    app.include_router(test_router, tags=["Test Execution"])
    
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} initialized")
    logger.info(f"📝 Debug mode: {settings.DEBUG}")
    logger.info(f"🌍 CORS origins: {settings.CORS_ORIGINS}")
    
    return app

# Create the app instance
app = create_app()
