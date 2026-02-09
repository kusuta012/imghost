from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.routes import upload
from app.core.config import settings

app = FastAPI(
    title="SpeedHawks's Image Host",
    description="Just a random backend",
    version="1.6.7",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)

@app.get("/")
async def root():
    return {"message": "Image Host API Running", "documentation": "/docs"}


# nginx config below soon

