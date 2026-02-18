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

BATCH_SIZE = 100
S3_CONC = 10
RETENTION_DAYS = 90

async def soft_delete_expired_imges():
    now = datetime.now(timezone.utc)
    deleted_total = 0
    failed_total = 0
    purge_urls_buffer: list[str] = [] 
    
    
    async with AsyncSessionLocal() as session:
        while True:
            stmt = (
                select(Image)
                .where(Image.expires_at < now, Image.deleted_at.is_(None))
                .limit(BATCH_SIZE)
            )
            result = await session.execute(stmt)
            batch = result.scalars().all()
        
            if not batch:
                break
        
        
            semaphore = asyncio.Semaphore(S3_CONC)
            
            async def delete_one(img: Image):
                nonlocal deleted_total, failed_total   
                try:
                    async with semaphore:
                        await storage_service.delete_file(img.filename)
                    img.deleted_at = datetime.now(timezone.utc)
                    img.object_url = "DELETED"

                    purge_urls_buffer.append(
                        f"{settings.PUBLIC_BASE_URL}/i/{img.filename}"
                    )
                    
                    deleted_total +=1
                except Exception as e:
                    failed_total += 1
                    logger.error(f"S3 delete failed for {img.filename}: {e}")
                    
            await asyncio.gather(*(delete_one(img) for img in batch))
            
            await session.commit()
            logger.info(f"Soft deleted batch of {len(batch)} images")
            
        logger.info(
            f"SOft delete complete deleted={deleted_total}, failed={failed_total}"
        )
        
    if purge_urls_buffer:
        try:
            purge_result = await purge_urls(purge_urls_buffer)
            logger.info("CLouflare purge result: %s", purge_result)
        except Exception:
            logger.error("cloudflare purge failed")
    
    
     
async def hard_delete_old_metadata():
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    
    async with AsyncSessionLocal() as session:
        stmt = select(Image).where(Image.deleted_at < cutoff_date)
        result = await session.execute(stmt)
        await session.commit()
        logger.info(f"Hard deleted {result.rowcount or 0 } old metadata rows")
        
async def print_stats():
    now = datetime.now(timezone.utc)
    next_hour = now + timedelta(hours=1)
    
    async with AsyncSessionLocal() as session:
        active = await session.scalar(
            select(func.count(Image.id)).where(
                Image.expires_at > now,
                Image.deleted_at.is_(None),
            )
        )
        
        deleted = await session.scalar(
            select(func.count(Image.id)).where(Image.deleted_at.is_not(None))
        )
        
        expiring = await session.scalar(
            select(func.count(Image.id)).where(
                Image.expires_at < next_hour,
                Image.expires_at > now,
                Image.deleted_at.is_(None),
                
            )
        )
        
    logger.info(
        f"Stats active={active}, soft-deleted={deleted}, expiring in 1h={expiring}"
    )
        
        
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
