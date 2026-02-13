import uuid
import magic
import logging
from typing import List, Annotated
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from slowapi.util import get_ipaddr
from db.session import limiter, get_db, custom_key_func
from core.config import settings
from models.image import Image
from services.storage import storage_service
from services.processing import process_image_and_update_db
from core.monitoring import UPLOAD_COUNT, ERROR_COUNT 

router = APIRouter()
logger = logging.getLogger("imghost")

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TOTAL_SIZE = 15 * 1024 * 1024
MAX_FILES = 10
MAX_IMAGES_PER_HOUR = 50  
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]


async def validate_file(file: UploadFile) -> tuple[bytes, str]:
    if hasattr(file, 'size') and file.size is not None:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File '{file.filename}' is too large (Max 5MB per file)"
            )
            
    head = await file.read(2048)
    mime_type = magic.Magic(mime=True).from_buffer(head)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File '{file.filename}' has invalid type: {mime_type}. Allowed: JPEG, PNG, WEBP, HEIC"
        )  

    await file.seek(0)
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' is too large (Max 5MB per file)"
        )
    return file_bytes, mime_type

# async def validate_and_read_file(file: UploadFile) -> tuple[bytes, str]:
#     file_bytes = await file.read()
    
#     if len(file_bytes) > MAX_FILE_SIZE:
#         raise HTTPException(
#             status_code=413, 
#             detail=f"File '{file.filename}' is too large (Max 5MB)"
#         )
    
#     mime_type = magic.Magic(mime=True).from_buffer(file_bytes)
#     if mime_type not in ALLOWED_MIME_TYPES:
#         raise HTTPException(
#             status_code=415, 
#             detail=f"File '{file.filename}' has invalid type: {mime_type}"
#         )
        
#     return file_bytes, mime_type

@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def upload_image(
    files: Annotated[List[UploadFile], File(description="images to upload")],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    ip_addr = custom_key_func(request)
    
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files! Max {MAX_FILES} allowed per upload"
        )
        
    total_size = sum(f.size for f in files if hasattr(f, 'size') and f.size)
    if total_size > MAX_TOTAL_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Total upload size ({total_size / (1024 * 1024):.2f} MB) exceeds the limit of 15MB"
        )
    
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    stmt = select(func.count(Image.id)).where(Image.ip_address == ip_addr, Image.uploaded_at >= one_hour_ago)
    result = await db.execute(stmt)
    recent_uploads = result.scalar() or 0 
    
    if recent_uploads + len(files) > MAX_IMAGES_PER_HOUR:
        remaining = MAX_IMAGES_PER_HOUR - recent_uploads
        raise HTTPException(
            status_code=429,
            detail=f"Upload limit exceeded. You've uploaded {recent_uploads}/{MAX_IMAGES_PER_HOUR} images in the last hour."
        )    
        
    results = []

    for file in files:
        try:
            file_bytes, mime_type = await validate_file(file)
            
            new_filename = str(uuid.uuid4())
            
            await storage_service.upload_file(BytesIO(file_bytes), new_filename, mime_type)

            new_image = Image(
                filename=new_filename,
                object_url=f"s3://{new_filename}", 
                size_bytes=len(file_bytes),
                mime_type=mime_type,
                is_processed=False,
                ip_address=ip_addr
            )
            db.add(new_image)
            
            await db.flush()

            background_tasks.add_task(
                process_image_and_update_db, 
                new_image.id, 
                file_bytes, 
                new_filename
            )
            
            results.append({"url": f"{settings.PUBLIC_BASE_URL}/i/{new_filename}"})
            UPLOAD_COUNT.inc()
            logger.info(f"Upload success.", extra={"status": 201, "ip": ip_addr, "img_filename": new_filename})

        except HTTPException as e:
            raise e
        except Exception as e:
            await db.rollback()
            ERROR_COUNT.inc()
            logger.error(f"Upload failed for {file.filename}: {e}", extra={"ip": ip_addr})
            raise HTTPException(status_code=500, detail="Internal server error during upload")

    await db.commit()
    
    total_uploaded_kb = sum(r.get('size', 0) for r in results) if results else 0
    logger.info(f"batch upload complete: {len(results)} files, {total_uploaded_kb/1024:.1f}MB toal", extra={"ip": ip_addr})
    return results