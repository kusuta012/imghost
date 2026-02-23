import io
import uuid
import logging
from PIL import Image as PilImage
from pillow_heif import register_heif_opener
from typing import Tuple
from services.storage import storage_service
from db.session import AsyncSessionLocal
from models.image import Image
from sqlalchemy import select
from services.cloudflare import purge_urls
from core.config import settings

logger = logging.getLogger("imghost.background")
MAX_DIMENSION = 2500

register_heif_opener() 

def strip_exif_and_process(file_bytes: bytes) -> Tuple[bytes, str]:
    logger.info("Starting image processing")


    try:
        img = PilImage.open(io.BytesIO(file_bytes))
        original_size = img.size
        data = list(img.getdata())
        img_no_exif = PilImage.new(img.mode, img.size)
        img_no_exif.putdata(data)

        width, height = img_no_exif.size
        needs_resize = width > MAX_DIMENSION or height > MAX_DIMENSION

        if needs_resize:
            if width > height:
                new_width = MAX_DIMENSION
                new_height = int((MAX_DIMENSION / width) * height)
            else:
                new_height = MAX_DIMENSION
                new_width = int((MAX_DIMENSION / height) * width)

            img_no_exif = img_no_exif.resize((new_width, new_height), PilImage.Resampling.LANCZOS)
            logger.info(f"Resized from {original_size} to {img_no_exif.size}")
            
        output_buffer = io.BytesIO()
        
        if img_no_exif.mode in ('RGBA', 'LA', 'P'):
            img_no_exif.save(output_buffer, format='WEBP', quality=85, method=6, lossless=False)
        else:
            if img_no_exif.mode != 'RGB':
                img_no_exif = img_no_exif.convert('RGB')   
            img_no_exif.save(output_buffer, format='WEBP', quality=85, method=6)

        output_buffer.seek(0)
        processed_bytes = output_buffer.read()
        
        original_kb = len(file_bytes) / 1024
        processed_kb = len(processed_bytes) / 1024
        reduction = ((len(file_bytes) - len(processed_bytes)) / len(file_bytes)) * 100
        
        logger.info(f"Original size: {original_kb:.2f} KB, Processed size: {processed_kb:.2f} KB, Reduction: {reduction:.2f}%")
        return processed_bytes, "image/webp"
    
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return file_bytes, "image/jpeg"
    

async def process_image_and_update_db(image_id: uuid.UUID, original_bytes: bytes, original_filename: str, original_mime: str):
    if original_mime == "image/gif":
        logger.info(f"skipping process for GIF {image_id}")
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Image).filter(Image.id == image_id)
                result = await session.execute(stmt)
                image = result.scalars().first()
                if image:
                    image.is_processed = True
                    await session.commit()
                    logger.info(f"Image {image_id} marked procesed (GIF)")
        except Exception as e:
            logger.exception(f"Failed gif process mark for {image_id}: {e}")
    
    
    processed_bytes, new_mime_type = strip_exif_and_process(original_bytes)
    
    size_reduction = len(original_bytes) - len(processed_bytes)
    reduction_pct = (size_reduction / len(original_bytes)) * 100
    
    if reduction_pct < 5:
        logger.info(f"Image {image_id} process resulted in ({reduction_pct:.2f}%) change, skipping reupload")
        async with AsyncSessionLocal() as session:
            stmt = select(Image).filter(Image.id == image_id)
            result = await session.execute(stmt)
            image = result.scalars().first()
            if image:
                image.is_processed = True
                await session.commit()
        return

    logger.info(f"Image {image_id} processed. New size: {len(processed_bytes)} bytes.")

    try:
        await storage_service.upload_file(
            file_obj=io.BytesIO(processed_bytes),
            filename=original_filename,
            mime_type=new_mime_type
        )
        
        try:
            public_url = f"{settings.PUBLIC_BASE_URL}/i/{original_filename}"
            purge_result = await purge_urls([public_url])
            logger.info(f"Purged CDN cache for {original_filename}: {purge_result}")
        except Exception as e:
            logger.exception(f"Failed to purge CDN cache for {original_filename}: {e}")
        
        async with AsyncSessionLocal() as session:
            stmt = select(Image).filter(Image.id == image_id)
            result = await session.execute(stmt)
            image = result.scalars().first()
    
            if image:
                image.size_bytes = len(processed_bytes)  # type: ignore[assignment]
                image.mime_type = new_mime_type
                image.is_processed = True

                await session.commit()
                logger.info(f"Image {image_id} DB updated successfully.")
            else:
                logger.warning(f"Image {image_id} not found for update (possible prior deletion).")

    except Exception as e:
        logger.critical(f"Background update failed for {image_id}: {e}")
