import time
import logging
import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from prometheus_client import Counter, Gauge, generate_latest # type: ignore

from app.services.storage import storage_service
from app.db.session import engine
from sqlalchemy import text

router = APIRouter(tags=["health_metrics"])
logger = logging.getLogger("imghost")

UPLOAD_COUNT = Counter('imghost_uploads_total', 'Total number of successful uploads')
DELETE_COUNT = Counter('imghost_deletes_total', 'Total number of successful deletes')
ERROR_COUNT = Counter('imghost_errors_total', 'Total number of internal errors')
REQUEST_LATENCY = Gauge('imghost_request_latency_seconds', 'Last successful request latency')

START_TIME = datetime.now(timezone.utc)

async def check_db_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            
        return True, "Database OK"
    except Exception as e:
        logger.error(f"DB check failed {e}")
        return False, str(e)
    
async def check_storage_connection():
    try:
        await storage_service.s3_client.list_buckets()
        return True, "Storage OK"
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        return False, str(e)
    
    
@router.get("/health")
async def health_check():
    db_ok, db_message = await check_db_connection()
    storage_ok, storage_message = await check_storage_connection()
    
    status_code = status.HTTP_200_OK
    overall_status = "OK"
    
    if not db_ok or not storage_ok:
        status_code= status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "UNAVAILABLE"
        
    uptime_seconds = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    
    return {
        "status": overall_status,
        "uptime_seconds": round(uptime_seconds),
        "database": {"status": "OK" if db_ok else "FAIL", "message": db_message},
        "storage": {"status": "OK" if storage_ok else "FAIL", "message": storage_message},
    }
    
# @router.get("/metrics")
# async def metrics():