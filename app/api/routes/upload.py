import uuid
import magic
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.image import Image
from app.services.storage import storage_service

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_MIME_TYPE = ["image/jpeg", "image/png", "image/webp"]


async def validate_file(file: UploadFile) -> bytes:
    
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the limit of {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
        )
        
    return file_bytes

def get_mime_type(file_bytes: bytes) -> str:
    try:
        mime = magic.Magic(mime=True).from_buffer(file_bytes)
        return mime
    except Exception:
        return "application/octet-stream"
    
    
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: Annotated[UploadFile, File(description="Image file to upload (JPEG , PNG or webP)")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    
    file_bytes = await validate_file(file)
    
    actual_mime_type = get_mime_type(file_bytes)
    
    if actual_mime_type not in ALLOWED_MIME_TYPE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {actual_mime_type}. Only JPEG, PNG, and WebP are allowed."      
        )
        
    image_id = uuid.uuid4()
    new_filename = str(image_id)
    
    try:
        
        from io import BytesIO
        file_buffer = BytesIO(file_bytes)
        
        object_url = await storage_service.upload_file(
            file_obj = file_buffer,
            filename=new_filename,
            mime_type=actual_mime_type
        )
        
        new_image = Image(
            filename=new_filename,
            object_url=object_url,
            size_bytes=len(file_bytes),
            mime_type=actual_mime_type,
        )
        
        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)

    except HTTPException:
        
        raise
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occured during processing."
        )
        
    public_url = f"{settings.PUBLIC_BASE_URL}/i/{new_filename}"
    
    return {"url": public_url}

