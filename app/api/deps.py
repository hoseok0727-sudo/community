from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.db import get_db


def get_admin_guard(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        return
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


DBSession = Depends(get_db)
AdminGuard = Depends(get_admin_guard)

