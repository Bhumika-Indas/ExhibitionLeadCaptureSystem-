"""
INDAS Exhibition Lead Capture System (ELCS)
FastAPI Backend Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings, init_storage
from app.db.connection import test_connection
from app.services.scheduler_service import init_scheduler, shutdown_scheduler, get_scheduler_status
from app.routers import (
    auth_router,
    leads_router,
    extraction_router,
    whatsapp_router,
    analytics_router,
    exhibitions_router,
    followup_router,
    websocket_router,
    drip_analytics_router,
    duplicates_router,
    drip_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 60)
    print(f" Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print("=" * 60)

    # Initialize storage directories
    init_storage()

    # Test database connection
    print(" Testing database connection...")
    if test_connection():
        print(" Database connected successfully")
    else:
        print(" Database connection failed!")

    # Initialize scheduler for automated tasks
    print(" Initializing task scheduler...")
    init_scheduler()

    yield

    # Shutdown
    print("\n Shutting down ELCS Backend...")
    shutdown_scheduler()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Exhibition Lead Capture System - Backend API",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving uploaded images/audio)
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router.router, prefix=settings.API_PREFIX)
app.include_router(exhibitions_router.router, prefix=settings.API_PREFIX)
app.include_router(leads_router.router, prefix=settings.API_PREFIX)
app.include_router(extraction_router.router, prefix=settings.API_PREFIX)
app.include_router(whatsapp_router.router)  # No prefix - accessible at /webhook
app.include_router(analytics_router.router, prefix=settings.API_PREFIX)
app.include_router(duplicates_router.router, prefix=settings.API_PREFIX)
app.include_router(followup_router.router)
app.include_router(drip_analytics_router.router)
app.include_router(drip_router.router, prefix=settings.API_PREFIX)
app.include_router(websocket_router.router)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "message": "Welcome to INDAS Exhibition Lead Capture System API"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()

    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION
    }


# Scheduler status
@app.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status and scheduled jobs"""
    return get_scheduler_status()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
