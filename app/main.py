from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_ipaddr
from slowapi.errors import RateLimitExceeded
from app.db.session import limiter, custom_key_func
from app.api.routes import upload, image, delete, health
from app.core.monitoring import PrometheusMiddleware
import logging, sys, json
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "status": getattr(record, 'status', None),
            "ip": getattr(record, 'ip', None),
            "filename": getattr(record, 'filename', None),
            }
        return json.dumps({k: v for k, v in log_record.items() if v is not None})
    
def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    logger = logging.getLogger("imghost")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers = [handler]
    uvicorn_logger.setLevel(logging.WARNING)
    
setup_logging()

app = FastAPI(
    title="SpeedHawks's Image Host",
    description="Just a random backend",
    version="1.6.7",
)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    logging.getLogger("imghost").warning(
        f"Rate Limit Exceeded.", 
        extra={"status": 429, "ip": custom_key_func(request), "path": request.url.path}
    )
    return _rate_limit_exceeded_handler(request, exc)

app.include_router(upload.router)
app.include_router(image.router)
app.include_router(delete.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "Image Host API Running", "documentation": "/docs"}



