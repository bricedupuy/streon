"""
Streon Controller - Main FastAPI Application

Professional Multi-Flow Audio Transport System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from api import flows, devices, stereotool, system, metadata
from core.config_manager import ConfigManager
from core.metadata_service import metadata_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Streon Controller...")

    # Initialize configuration
    config_mgr = ConfigManager()
    app.state.config = config_mgr.load_global_config()

    # Start metadata service
    logger.info("Starting Metadata Service...")
    await metadata_service.start()

    logger.info(f"Controller listening on {app.state.config.controller_host}:{app.state.config.controller_port}")
    logger.info("Streon Controller started successfully")

    yield

    # Cleanup
    logger.info("Shutting down Streon Controller...")

    # Stop metadata service
    logger.info("Stopping Metadata Service...")
    await metadata_service.stop()


# Create FastAPI application
app = FastAPI(
    title="Streon Controller API",
    description="Professional Multi-Flow Audio Transport System for Radio Broadcasters",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow all origins for now - restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": "Streon Controller API",
        "version": "1.0.0",
        "description": "Professional Multi-Flow Audio Transport System",
        "docs": "/docs",
        "health": "/api/v1/system/health"
    }


# Include routers
app.include_router(flows.router, prefix="/api/v1", tags=["Flows"])
app.include_router(devices.router, prefix="/api/v1", tags=["Devices"])
app.include_router(stereotool.router, prefix="/api/v1", tags=["StereoTool"])
app.include_router(metadata.router, prefix="/api/v1", tags=["Metadata"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
