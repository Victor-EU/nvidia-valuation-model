"""
CLI Script to run database seeding from Excel.

Usage:
    python -m app.seed.run_seed
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import async_session_factory, engine, Base
from app.seed.seed_from_excel import seed_all_from_excel, EXCEL_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    """Run the seeding process."""
    logger.info("Starting database seeding process")

    # Check if Excel file exists
    if not EXCEL_FILE.exists():
        logger.error(f"Excel file not found: {EXCEL_FILE}")
        logger.error("Please ensure NvidiaJan2025.xlsx is in the data/ directory")
        sys.exit(1)

    # Initialize database
    await init_db()

    # Run seeding
    async with async_session_factory() as session:
        summary = await seed_all_from_excel(session)

    logger.info("Seeding completed successfully!")
    logger.info(f"Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
