import time
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

UPLOAD_COUNT = Counter('imghost_uploads_total', 'Total number of successful uploads')
DELETE_COUNT = Counter('imghost_deletes_total', 'Total number of successful deletes')
ERROR_COUNT = Counter('imghost_errors_total', 'Total number of intersnal errors')
REQUEST_LATENCY = Histogram(
    'imghost_request_latency_seconds', 
    'Request latency distribution', 
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()
        
        if request.url.path != "/metrics":
            REQUEST_LATENCY.observe(end_time - start_time)
            
        return response
    
    