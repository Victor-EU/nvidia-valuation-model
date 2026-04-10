"""
NVIDIA Valuation Model API

FastAPI application for DCF valuation calculations.
Build: 2026-04-10 — auto-deploy test
"""

import asyncio
import logging
import os
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


async def _init_database():
    """Initialize database tables and seed data (runs in background)."""
    try:
        from app.database import engine, Base, AsyncSessionLocal
        if engine is None:
            logger.warning("Database engine not available — skipping initialization")
            return

        import app.models.country  # noqa: F401
        import app.models.industry  # noqa: F401
        import app.models.synthetic_rating  # noqa: F401
        import app.models.valuation_model  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created")

        try:
            from app.seed.seed_from_excel import seed_all_from_excel, EXCEL_FILE
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT COUNT(*) FROM countries"))
                count = result.scalar()
                if count == 0 and EXCEL_FILE.exists():
                    logger.info("Empty reference tables detected — seeding from Excel...")
                    summary = await seed_all_from_excel(session)
                    logger.info(f"Auto-seed complete: {summary}")
                elif count == 0:
                    logger.warning("Reference tables empty but Excel file not found at %s", EXCEL_FILE)
        except Exception as e:
            logger.warning("Auto-seed check failed (non-fatal): %s", e)
    except Exception as e:
        logger.error("Database initialization failed (non-fatal): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — starts DB init in background."""
    logger.info("Starting NVIDIA Valuation Model API")
    logger.info("DATABASE_URL configured: %s", "yes" if os.getenv("DATABASE_URL") else "no (using SQLite)")
    # Run DB init in background so the app starts accepting requests immediately
    task = asyncio.create_task(_init_database())
    yield
    task.cancel()
    logger.info("Shutting down NVIDIA Valuation Model API")


app = FastAPI(
    title="NVIDIA Valuation Model API",
    description="DCF valuation model API replicating Damodaran's Excel model",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
cors_origins = settings.cors_origins.copy()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (no /api prefix — the reverse proxy handles prefix stripping)
app.include_router(models.router, prefix="/models", tags=["Models"])
app.include_router(calculations.router, prefix="/calculate", tags=["Calculations"])
app.include_router(reference.router, prefix="/reference", tags=["Reference Data"])
app.include_router(data.router, prefix="/data", tags=["Data Fetching"])


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
