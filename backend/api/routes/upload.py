import uuid
import magic
import logging
import tempfile
import os
from typing import List, Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from db.session import limiter, get_db, custom_key_func
from core.config import settings
from models.image import Image
from services.storage import storage_service
from services.processing import process_image_and_update_db
from core.monitoring import UPLOAD_COUNT, ERROR_COUNT 

router = APIRouter()
logger = logging.getLogger("imghost")

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_GIF_SIZE = 25 * 1024 * 1024
MAX_TOTAL_SIZE = 15 * 1024 * 1024
MAX_FILES = 10
MAX_IMAGES_PER_HOUR = 50  
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "image/gif"]


async def validate_file(file: UploadFile) -> str:
            
    head = await file.read(2048)
    mime_type = magic.Magic(mime=True).from_buffer(head)
    await file.seek(0)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File '{file.filename}' has invalid type: {mime_type}. Allowed: JPEG, PNG, WEBP, HEIC/HEIF, GIF"
        )  
    return mime_type


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def upload_image(
    files: Annotated[List[UploadFile], File(description="images to upload")],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    expires_minutes: Annotated[str | None, Form(description="Expiry in minutes")] = None
):
    ip_addr = custom_key_func(request)

    
    if expires_minutes is None:
        expires_minutes_int = 1440 
    else:
        try:
            expires_minutes_int = int(expires_minutes)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="expires_minutes must be an integer"
            )

        if expires_minutes_int < 5 or expires_minutes_int > 24 * 60:
            raise HTTPException(
                status_code=400,
                detail="Expiry must be between 5 minutes and 1440 minutes (24 hours)"
            )

    computed_expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes_int)
    
    
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
    
    async def process_tmp(image_id: uuid.UUID, tmp_path: str, filename: str, original_mime: str):
        try:
            with open(tmp_path, 'rb') as f:
                file_bytes = f.read()
            await process_image_and_update_db(image_id, file_bytes, filename, original_mime)
        except Exception as e:
            logger.error(f"Background processing failed for {filename}: {e}", exc_info=True)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Failed to delete temp file {tmp_path}: {e}")

    for file in files:
        tmp_path = None
        new_filename = str(uuid.uuid4())
        try:
            mime_type = await validate_file(file)
            
            per_file_limit = MAX_GIF_SIZE if mime_type == "image/gif" else MAX_FILE_SIZE
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
                written = 0
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    tmp.write(chunk)
                    written += len(chunk)
                    if written > per_file_limit:
                        tmp.close()
                        try:
                            os.unlink(tmp_path)
                        except Exception as e:
                            pass
                        raise HTTPException(status_code=413, detail=f"File '{file.filename}' is too large (Max 5MB per file and Max 25MB for GIF)")
                tmp.flush()
                
                
            with open(tmp_path, 'rb') as fh:
                await storage_service.upload_file(fh, new_filename, mime_type)
                
            file_size = os.path.getsize(tmp_path)
            
            new_image = Image(
                filename=new_filename,
                object_url=f"s3://{new_filename}", 
                size_bytes=file_size,
                mime_type=mime_type,
                is_processed=False,
                ip_address=ip_addr,
                expires_at=computed_expires_at
            )

                
            db.add(new_image)
            await db.flush()

            background_tasks.add_task(
                process_tmp, 
                new_image.id, 
                tmp_path, 
                new_filename,
                mime_type
            )
            
            resp_item = {
                "url": f"{settings.PUBLIC_BASE_URL}/i/{new_filename}",
                "size": file_size,
                "mime_type": mime_type 
            }
            
            if computed_expires_at is not None:
                resp_item["expires_at"] = computed_expires_at.isoformat()
                
            results.append(resp_item)
            
            # results.append({"url": f"{settings.PUBLIC_BASE_URL}/i/{new_filename}", "size": file_size})
            UPLOAD_COUNT.inc()
            logger.info(f"Upload success.", extra={"status": 201, "ip": ip_addr, "img_filename": new_filename})

            tmp_path = None

        except HTTPException as e:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            raise e
        except Exception as e:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            await db.rollback()
            ERROR_COUNT.inc()
            logger.error(f"Upload failed for {file.filename}: {e}", extra={"ip": ip_addr}, exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error during upload")

    await db.commit()
    
    total_uploaded_mb = sum(r.get('size', 0) for r in results) / 1024 * 1024 if results else 0
    logger.info(f"batch upload complete: {len(results)} files, {total_uploaded_mb:.1f}MB toal", extra={"ip": ip_addr})
    return results