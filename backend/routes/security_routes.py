"""Security configuration routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import require_api_key
from security import (
    get_allowed_directories,
    add_allowed_directory,
    is_path_allowed,
)

router = APIRouter(prefix="/security", tags=["Security"])


class AllowedDirectoryRequest(BaseModel):
    path: str


@router.get("/allowed-directories", dependencies=[Depends(require_api_key)])
def get_allowed_scan_directories():
    """Get list of allowed scan directories."""
    return {"directories": get_allowed_directories()}


@router.post("/allowed-directories", dependencies=[Depends(require_api_key)])
def add_allowed_scan_directory(request: AllowedDirectoryRequest):
    """Add a directory to the allowed scan list."""
    try:
        add_allowed_directory(request.path)
        return {"added": True, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-path", dependencies=[Depends(require_api_key)])
def validate_path(request: AllowedDirectoryRequest):
    """Check if a path is allowed for scanning."""
    return {"allowed": is_path_allowed(request.path)}
