import logging
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from prometheus_client import generate_latest

from services.storage import storage_service
from db.session import engine
from sqlalchemy import text

router = APIRouter(tags=["health_metrics"])
logger = logging.getLogger("imghost")

START_TIME = datetime.now(timezone.utc)

async def check_db_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Database OK"
    except Exception as e:
        logger.error(f"Health check DB failed: {e}")
        return False, str(e)

async def check_storage_connection():
    try:
        await asyncio.to_thread(storage_service.s3_client.list_buckets)
        return True, "Storage OK"
    except Exception as e:
        logger.error(f"Health check Storage failed: {e}")
        return False, str(e)


@router.get("/health")
async def health_check():
    db_ok, db_message = await check_db_connection()
    storage_ok, storage_message = await check_storage_connection()
    
    status_code = status.HTTP_200_OK
    overall_status = "OK"
    
    if not db_ok or not storage_ok:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "UNAVAILABLE"
        
    uptime_seconds = (datetime.now(timezone.utc) - START_TIME).total_seconds()

    return {
        "status": overall_status,
        "uptime_seconds": round(uptime_seconds),
        "database": {"status": "OK" if db_ok else "FAIL", "message": db_message},
        "storage": {"status": "OK" if storage_ok else "FAIL", "message": storage_message},
    }

@router.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )