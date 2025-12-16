from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
import time
import logging

from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Source as DBSource
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway health checks"""
    return {
        "status": "healthy",
        "message": "API is operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""
    try:
        # Database connectivity check
        db_start = time.time()
        db.execute(text("SELECT 1"))
        db_time = time.time() - db_start

        # System metrics (optional - requires psutil)
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            psutil_available = True
        except ImportError:
            psutil_available = False
            memory = None
            cpu_percent = None

        # Database stats
        claim_count = db.query(func.count(DBClaim.id)).scalar() or 0
        source_count = db.query(func.count(DBSource.id)).scalar() or 0

        system_info = {}
        if psutil_available and memory and cpu_percent is not None:
            system_info = {
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu_percent,
                "memory_used_mb": memory.used // (1024 * 1024),
                "memory_total_mb": memory.total // (1024 * 1024),
                "uptime_seconds": time.time() - psutil.boot_time(),
            }
        else:
            system_info = {
                "note": "psutil not available - system metrics disabled"
            }

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "system": system_info,
            "database": {
                "connection_time_ms": round(db_time * 1000, 2),
                "claims_count": claim_count,
                "sources_count": source_count,
            },
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        # Return degraded status but don't fail the check
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "Some health checks failed but service is operational"
        }
