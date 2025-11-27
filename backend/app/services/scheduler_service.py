"""
APScheduler Service for Automated Tasks
Handles periodic execution of follow-up processing and other scheduled tasks
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.services.followup_service import followup_service
import logging
import httpx

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_scheduler():
    """Initialize and start the scheduler"""
    global scheduler

    scheduler = AsyncIOScheduler()

    # Job 1: Process pending follow-ups every hour
    scheduler.add_job(
        process_followups_job,
        trigger=CronTrigger(minute=0),  # Run at the start of every hour
        id="process_followups",
        name="Process Pending Follow-ups",
        replace_existing=True
    )

    # Job 2: Process drip messages every 5 minutes
    scheduler.add_job(
        process_drip_messages_job,
        trigger=CronTrigger(minute="*/5"),  # Run every 5 minutes
        id="process_drip_messages",
        name="Process Drip Messages",
        replace_existing=True
    )

    # Job 3: Daily cleanup (optional - for future use)
    # scheduler.add_job(
    #     daily_cleanup_job,
    #     trigger=CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
    #     id="daily_cleanup",
    #     name="Daily Database Cleanup",
    #     replace_existing=True
    # )

    scheduler.start()
    print(" Scheduler initialized and started")
    print(" Scheduled jobs:")
    for job in scheduler.get_jobs():
        print(f"   - {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")

    logger.info(" Scheduler initialized and started")
    logger.info(" Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"   - {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler

    if scheduler:
        scheduler.shutdown()
        logger.info(" Scheduler shut down")


async def process_followups_job():
    """
    Scheduled job to process pending follow-ups
    Runs every hour
    """
    try:
        logger.info(f"⏰ [CRON] Starting follow-up processing at {datetime.now()}")

        processed = await followup_service.process_pending_followups()

        logger.info(f"✓ [CRON] Processed {processed} follow-ups successfully")

    except Exception as e:
        logger.error(f"✗ [CRON] Follow-up processing failed: {str(e)}")


async def process_drip_messages_job():
    """
    Scheduled job to process pending drip messages
    Runs every 5 minutes
    """
    try:
        logger.info(f"⏰ [CRON] Starting drip message processing at {datetime.now()}")

        # Call the drip process endpoint
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post('http://localhost:8000/api/drip/process')
            result = response.json()

            processed = result.get('processed', 0)
            failed = result.get('failed', 0)

            logger.info(f"✓ [CRON] Drip messages: {processed} sent, {failed} failed")

    except Exception as e:
        logger.error(f"✗ [CRON] Drip message processing failed: {str(e)}")


async def daily_cleanup_job():
    """
    Optional daily cleanup job
    Can be used for database maintenance, log rotation, etc.
    """
    try:
        logger.info(f" [CRON] Starting daily cleanup at {datetime.now()}")

        # Add cleanup tasks here
        # Example: Delete old temporary files, archive old data, etc.

        logger.info(" [CRON] Daily cleanup completed")

    except Exception as e:
        logger.error(f" [CRON] Daily cleanup failed: {str(e)}")


def get_scheduler_status():
    """Get current scheduler status and job info"""
    global scheduler

    if not scheduler or not scheduler.running:
        return {
            "status": "stopped",
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "status": "running",
        "jobs": jobs
    }
