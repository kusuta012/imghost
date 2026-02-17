import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from db.session import AsyncSessionLocal
from models.image import Image
from services.storage import storage_service
from services.cloudflare import purge_urls
from core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cleanup")

async def soft_delete_expired_imges():
    async with AsyncSessionLocal() as session:
        stmt = select(Image).where(
            Image.expires_at < datetime.now(timezone.utc),
            Image.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        expired = result.scalars().all()
        
        if not expired:
            logger.info("No expired images found for soft deletion")
            return
        
        deleted_count = 0
        failed_count = 0
        to_purge = []
        
        for img in expired:
            try:
        
                await storage_service.delete_file(img.filename)
                img.deleted_at = datetime.now(timezone.utc)
                img.object_url = "DELETED"
                public_url = f"{settings.PUBLIC_BASE_URL}/i/{img.filename}"
                to_purge.append(public_url)
                deleted_count += 1
                logger.info(f"Soft delete: {img.filename} | Uploaded: {img.uploaded_at} | (IP: {img.ip_address})")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to soft delete {img.filename}: {e}")
                
        await session.commit()
        logger.info(f"Completed cleanup: {deleted_count} deleted, {failed_count} failed")
        
        if to_purge:
            try:
                purge_results = await purge_urls(to_purge)
                logger.info("CLoudflare purge results: %s", purge_results)
            except Exception as e:
                logger.error("Cloudflare purge call failed: %s", e, exc_info=True)
        
async def hard_delete_old_metadata():
    retention_days = 90
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    async with AsyncSessionLocal() as session:
        stmt = select(Image).where(
            Image.deleted_at < cutoff_date,
            Image.deleted_at.is_not(None)
        )
        result = await session.execute(stmt)
        old_records = result.scalars().all()
        
        if not old_records:
            logger.info("No old metadata records found for hard deletion")
            return
        
        for img in old_records:
            try:
                await session.delete(img)
                logger.info(f"Hard delete metadata: {img.filename} (originally uploaded at {img.uploaded_at})")
            except Exception as e:
                logger.error(f"Failed to hard delete metadata for {img.filename}: {e}")

        await session.commit()
        logger.info(f"Hard deleted {len(old_records)} metadata records")
        
async def print_stats():
    async with AsyncSessionLocal() as session:
        active_stmt = select(func.count(Image.id)).where(Image.expires_at > datetime.now(timezone.utc), Image.deleted_at.is_(None))
        active_result = await session.execute(active_stmt)
        active_count = active_result.scalar()
        
        deleted_stmt = select(func.count(Image.id)).where(Image.deleted_at.is_not(None))
        deleted_result = await session.execute(deleted_stmt)
        deleted_count = deleted_result.scalar()
        
        next_hour = datetime.now(timezone.utc) + timedelta(hours=1)
        expiring_stmt = select(func.count(Image.id)).where(Image.expires_at < next_hour, Image.expires_at > datetime.now(timezone.utc), Image.deleted_at.is_(None))
        expiring_result = await session.execute(expiring_stmt)
        expiring_count = expiring_result.scalar()
        
        logger.info(f"Stats: {active_count} active images | {deleted_count} soft deleted | {expiring_count} expiring within 1hr")
        
async def main():
    logger.info("Starting cleanup job.....")
    try:
        await print_stats()
        await soft_delete_expired_imges()
        await hard_delete_old_metadata()
        await print_stats()
        logger.info("Cleanup job completed successfully")
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}", exc_info=True)
        raise 
  
if __name__ == "__main__":
    asyncio.run(main())