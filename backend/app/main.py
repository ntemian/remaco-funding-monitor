"""Remaco EU Funding Monitor — FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.models.database import init_db, async_session
from app.api.routes import router
from app.services.pipeline import DailyPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
STATIC_DIR = Path(__file__).parent.parent / "static"


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve React frontend from /static
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve static files, fall back to index.html for SPA routing."""
        file_path = STATIC_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}
