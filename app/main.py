from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import BaseAPIException
from app.core.exception_handlers import (
    base_api_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    boto_exception_handler,
    generic_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown events."""
    if settings.auto_init_db:
        try:
            from scripts.init_db import init_database
            print("Initializing database...")
            success = init_database()
            if success:
                print("✓ Database initialization completed successfully")
            else:
                print("⚠ Database initialization had issues, but continuing...")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize database automatically: {e}")
            print("  The application will continue, but database operations may fail.")
            print("  Ensure your .env file is configured correctly.")
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


app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(ClientError, boto_exception_handler)
app.add_exception_handler(BotoCoreError, boto_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Document Analyzer Platform API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


