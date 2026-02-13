import uuid
from sqlalchemy import String, Integer, TIMESTAMP, text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base
from datetime import datetime

class Image(Base):
    __tablename__ = "images"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    filename: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    object_url: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[str] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text("now() + interval '24 hours'")
    ) 
    
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_expires_at', expires_at),
        Index('idx_deleted_at', deleted_at),
        Index('idx_is_processed', is_processed)
    )
     
    def __repr__(self) -> str:
        return f"<Image(id={self.id}, filename='{self.filename}')>"
    
    