"""
NVIDIA Valuation Model API

FastAPI application for DCF valuation calculations.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import models, calculations, reference, data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting NVIDIA Valuation Model API")
    yield
    logger.info("Shutting down NVIDIA Valuation Model API")


app = FastAPI(
    title="NVIDIA Valuation Model API",
    description="DCF valuation model API replicating Damodaran's Excel model",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(calculations.router, prefix="/api/calculate", tags=["Calculations"])
app.include_router(reference.router, prefix="/api/reference", tags=["Reference Data"])
app.include_router(data.router, prefix="/api/data", tags=["Data Fetching"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "NVIDIA Valuation Model API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
