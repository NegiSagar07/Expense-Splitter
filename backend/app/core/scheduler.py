"""
app/core/scheduler.py
----------------------
In-process background task scheduler powered by APScheduler.

Background jobs:
  - Join Request Expiry Sweep (FR4a): Sweeps `join_requests` where status is PENDING
    and `requested_at` is older than JOIN_REQUEST_EXPIRY_DAYS (default 7 days) and
    marks them EXPIRED.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import update

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.models import JoinRequest, JoinRequestStatus

logger = logging.getLogger("expense_splitter.scheduler")
settings = get_settings()

scheduler = AsyncIOScheduler()


async def sweep_expired_join_requests() -> None:
    """
    Find and update all pending join requests older than JOIN_REQUEST_EXPIRY_DAYS to EXPIRED.
    Runs periodically in the background (FR4a).
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=settings.JOIN_REQUEST_EXPIRY_DAYS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(JoinRequest)
            .where(
                JoinRequest.status == JoinRequestStatus.PENDING,
                JoinRequest.requested_at <= cutoff,
            )
            .values(
                status=JoinRequestStatus.EXPIRED,
                resolved_at=datetime.now(tz=timezone.utc),
            )
        )
        await session.commit()
        count = result.rowcount
        if count > 0:
            logger.info("Swept %d expired join requests (older than %d days).", count, settings.JOIN_REQUEST_EXPIRY_DAYS)


def start_scheduler() -> None:
    """Start the APScheduler background worker."""
    if not scheduler.running:
        # Run sweep every 1 hour (or 5 minutes for rapid development)
        scheduler.add_job(
            sweep_expired_join_requests,
            "interval",
            minutes=30,
            id="join_request_expiry_sweep",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background APScheduler started.")


def stop_scheduler() -> None:
    """Shutdown the scheduler cleanly."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background APScheduler stopped.")
