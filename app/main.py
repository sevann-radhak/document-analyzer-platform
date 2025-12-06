from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_init_db:
        try:
            from scripts.init_db import init_database
            init_database()
        except Exception as e:
            print(f"Warning: Could not initialize database automatically: {e}")
            print("  You may need to run 'python scripts/init_db.py' manually")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Document Analyzer Platform API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


