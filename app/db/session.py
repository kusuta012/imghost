from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.core.config import settings
from slowapi import Limiter
from slowapi.util import get_ipaddr

def custom_key_func(request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    return get_ipaddr(request)

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker (
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

limiter = Limiter(key_func=custom_key_func, default_limits=[], storage_uri=settings.RATE_LIMIT_STORAGE_URL) 

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
    