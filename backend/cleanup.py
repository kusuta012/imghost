import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from db.session import AsyncSessionLocal
from models.image import Image
from services.storage import storage_service

logging.basicConfig(level=logging.INFO)
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
        
        for img in expired:
            try:
                
                await storage_service.delete_file(img.filename)
                img.deleted_at = datetime.now(timezone.utc)
                img.object_url = "DELETED"
                
                logger.info(f"Soft delete: {img.filename} (IP: {img.ip_address})")
            except Exception as e:
                logger.error(f"Failed to soft delete {img.filename}: {e}")
                
        await session.commit()
        logger.info(f"Soft deleted {len(expired)} images")
        
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
 
async def main():
    logger.info("Starting cleanup job.....")
    await soft_delete_expired_imges()
    await hard_delete_old_metadata()
    logger.info("Cleanup job completed") 
  
if __name__ == "__main__":
    asyncio.run(main())