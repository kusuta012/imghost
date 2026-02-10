import io
import uuid
import logging
from PIL import Image as PilImage, ExifTags
from typing import Tuple, BinaryIO
from backend.services.storage import storage_service
from backend.db.session import AsyncSessionLocal
from backend.models.image import Image
from sqlalchemy import select

logger = logging.getLogger("imghost.background")


def strip_exif_and_process(file_bytes: bytes) -> Tuple[bytes, str]:
    logger.info("Starting image processing")
    
    output_format = "JPEG"
    mime_type = "image/jpeg"
    
    try:
        img = PilImage.open(io.BytesIO(file_bytes))
        
        data = list(img.getdata())
        img_no_exif = PilImage.new(img.mode, img.size)
        img_no_exif.putdata(data)
        
        img_format = img.format.lower() if img.format else ''
        if 'webp' in img_format or img_no_exif.mode in ('RGB', 'RGBA'):
            output_format = "WEBP"
            mime_type = "image/webp"
            
        output_buffer = io.BytesIO()
        
        if output_format == "WEBP":
            img_no_exif.save(output_buffer, format='WEBP', optimize=True, quality=90)
        else:
            
            if img_no_exif.mode in ('RGBA', 'P'):
                img_no_exif = img_no_exif.convert('RGB')
            img_no_exif.save(output_buffer, format='JPEG', optimize=True, quality=90)
            
        output_buffer.seek(0)
        return output_buffer.read(), mime_type
    
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        
        return file_bytes, mime_type
    
async def process_image_and_update_db(image_id: uuid.UUID, original_bytes: bytes, original_filename: str):
    processed_bytes, new_mime_type= strip_exif_and_process(original_bytes)
    

    if len(processed_bytes) == len(original_bytes):
        logger.info(f"Image {image_id} processing resulted in no material change.")
        return
    
    logger.info(f"Image {image_id} processed. New size: {len(processed_bytes)} bytes.")
    
    try:
        await storage_service.upload_file(
            file_obj=io.BytesIO(processed_bytes),
            filename=original_filename,
            mime_type=new_mime_type
        )
        
        async with AsyncSessionLocal() as session:
            stmt = select(Image).filter(Image.id == image_id)
            result = await session.execute(stmt)
            image = result.scalars().first()
            
            if image:
                image.size_bytes = len(processed_bytes) # type: ignore[assignment]
                image.mime_type = new_mime_type
                image.is_processed = True
                
                await session.commit()
                logger.info(f"Image {image_id} DB updated successfully.")
            else:
                logger.warning(f"Image {image_id} not found for update (possible prior deletion).")
                
    except Exception as e:
        logger.critical(f"Background update failed for {image_id}: {e}")
        
        