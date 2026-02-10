import uuid
import magic
import bcrypt
import logging
import secrets
from typing import Annotated
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi.util import get_ipaddr
from app.db.session import limiter
from app.core.config import settings
from app.db.session import get_db
from app.models.image import Image
from app.services.storage import storage_service
from app.services.processing import process_image_and_update_db
from app.core.monitoring import UPLOAD_COUNT, ERROR_COUNT 

router = APIRouter()
logger = logging.getLogger("imghost")

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]


async def validate_file(file: UploadFile) -> bytes:
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the limit")
    return file_bytes

def get_mime_type(file_bytes: bytes) -> str:
    try:
        return magic.Magic(mime=True).from_buffer(file_bytes)
    except Exception:
        return "application/octet-stream"

@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def upload_image(
    file: Annotated[UploadFile, File(description="Image file to upload")],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    request
):
    ip_addr = get_ipaddr(request)
    
    try:
        file_bytes = await validate_file(file)
    except HTTPException as e:
        logger.warning(f"Upload rejected: Size limit exceeded.", extra={"status": e.status_code, "ip": ip_addr})
        raise
    
    actual_mime_type = get_mime_type(file_bytes)
    
    if actual_mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Upload rejcted: Unsupported file type {actual_mime_type}.", extra={"status": 415, "ip": ip_addr})
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {actual_mime_type}"
        )

    image_id = uuid.uuid4()
    new_filename = str(image_id) 
    clear_token = secrets.token_hex(32)
    
    salt = bcrypt.gensalt()
    token_hash = bcrypt.hashpw(clear_token.encode('utf-8'), salt).decode('utf-8')

    try:
        file_buffer = BytesIO(file_bytes)
        
        object_url = await storage_service.upload_file(
            file_obj=file_buffer,
            filename=new_filename,
            mime_type=actual_mime_type
        )

        new_image = Image(
            filename=new_filename,
            object_url=object_url,
            size_bytes=len(file_bytes),
            mime_type=actual_mime_type,
            delete_token_hash=token_hash,
            is_processed=False
        )
        
        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)

        background_tasks.add_task(
            process_image_and_update_db, 
            new_image.id, 
            file_bytes, 
            new_filename
        )
        
        UPLOAD_COUNT.inc()
        logger.info(f"Upload success.", extra={"status": 201, "ip": ip_addr, "filename": new_filename})

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback() 
        ERROR_COUNT.inc() 
        logger.error(f"Upload failed: DB/System error - {e}", extra={"status": 500, "ip": ip_addr})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during processing"
        )

    public_url = f"{settings.PUBLIC_BASE_URL}/i/{new_filename}"

    return {
        "url": public_url,
        "delete_token": clear_token
    }