"""
Health check task for monitoring Celery worker status
"""
from celery import shared_task
from app.database import SessionLocal
from sqlalchemy import text
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def health_check():
    """Simple health check task to verify worker is alive and can access database"""
    try:
        db = SessionLocal()
        # Simple query to verify database connection
        result = db.execute(text("SELECT 1")).scalar()
        db.close()
        
        if result == 1:
            logger.info("Health check passed")
            return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
        else:
            logger.warning("Health check failed: unexpected result")
            return {"status": "unhealthy", "error": "unexpected_result"}
            
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {"status": "unhealthy", "error": str(e)}

