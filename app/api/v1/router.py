from fastapi import APIRouter
from app.api.v1.endpoints import auth, files, tokens, documents

api_router = APIRouter(prefix="/api/v1", tags=["v1"])

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"]
)

api_router.include_router(
    tokens.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)


