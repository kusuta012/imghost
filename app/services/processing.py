import io
import uuid
from PIL import Image as PilImage, ExifTags
from typing import Tuple, BinaryIO
from app.services.storage import storage_service
from app.db.session import AsyncSessionLocal
from app.models.image import Image
from sqlalchemy import select

def log_background_task(level: str, message: str):
    print(f"[{level}] [Background Task] {message}")
    
def strip_exif_and_process(file_bytes: bytes) -> Tuple[bytes, str]:
    log_background_task("INFO", "Starting image processing")
    
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
        log_background_task("ERROR", f"Image processing failed: {e}")
        
        return file_bytes, mime_type
    
async def process_image_and_update_db(image_id: uuid.UUID, original_bytes: bytes, original_filename: str):
    processed_bytes, new_mime_type= strip_exif_and_process(original_bytes)
    

    if len(processed_bytes) == len(original_bytes):
        log_background_task("INFO", f"Image {image_id} processing resulted in no change")
        return
    
    log_background_task("INFO", f"image {image_id} processed. New size: {len(processed_bytes)} bytes.")
    
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
                log_background_task("INFO", f"Image {image_id} DB Updated sucessfully")
            else:
                log_background_task("WARNING", f"Image {image_id} not found for update")
                
    except Exception as e:
        log_background_task("CRITICAL", f"Background update failed for {image_id} {e}")
        
        