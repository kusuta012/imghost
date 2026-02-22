from fastapi import FastAPI
import sentry_sdk
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from db.session import limiter, custom_key_func
from api.routes import upload, health
from core.monitoring import PrometheusMiddleware
from services.cloudflare import close_client
import logging, sys, json, os
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
            "img_filename": getattr(record, 'img_filename', None),
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

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    enable_logs=True,
    traces_sample_rate=0.7,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)


app = FastAPI(
    title="SpeedHawks's Image Host",
    description="Just a random backend",
    version="1.6.7",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://imghost.app"],
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
app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "Image Host API Running"}

@app.on_event("shutdown")
async def shutdown_event():
    await close_client()


