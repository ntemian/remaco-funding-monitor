"""Remaco EU Funding Monitor — FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.models.database import init_db, async_session
from app.api.routes import router
from app.services.pipeline import DailyPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_pipeline():
    """Run the daily pipeline as a scheduled job."""
    logger.info("Scheduled pipeline run starting...")
    async with async_session() as db:
        pipeline = DailyPipeline(db)
        stats = await pipeline.run(days_back=1)
        logger.info(f"Scheduled pipeline complete: {stats}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")

    # Schedule daily pipeline
    scheduler.add_job(
        scheduled_pipeline,
        "cron",
        hour=settings.DAILY_SCAN_HOUR,
        minute=settings.DAILY_SCAN_MINUTE,
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — daily scan at {settings.DAILY_SCAN_HOUR:02d}:{settings.DAILY_SCAN_MINUTE:02d}")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Daily EU & Greek funding call aggregator with eligibility matching",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
