import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from db.session import AsyncSessionLocal
from models.image import Image
from services.storage import storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

async def purge_expired_images():
    async with AsyncSessionLocal() as session:
        stmt = select(Image).where(Image.expire_at < datetime.now(timezone.utc))
        result = await session.execute(stmt)
        expired = result.scalars().all()
        
        if not expired:
            logger.info("No expired imagea found")
            return
        
        for img in expired:
            try:
                await storage_service.delete_file(img.filename)
                await session.delete(img)
                logger.info(f"Purge: {img.filename}")
            except Exception as e:
                logger.error(f"Failed to purge {img.filename}: {e}")
                
        await session.commit()
        
if __name__ == "__main__":
    asyncio.run(purge_expired_images())