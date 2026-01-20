from fastapi import Header, HTTPException, status, Depends
import os

from utils_telegram_webapp_auth import verify_telegram_webapp


ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")


async def require_admin(x_admin_secret: str = Header(..., alias="X-Admin-Secret")) -> None:
    """Simple header-based admin guard for /api/admin routes.

    Any admin endpoint should include: dependencies=[Depends(require_admin)].
    """
    if not ADMIN_SECRET:
        # If no secret is configured, deny by default instead of opening admin by accident
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access disabled")

    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def require_telegram_webapp(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
) -> dict:
    """Validate Telegram WebApp initData for requests coming from WebApp.

    Use as a dependency for endpoints wywoływane bezpośrednio z WebAppa (np. POST /api/orders).
    Returns parsed initData dict if valid, otherwise 403.
    """
    try:
        data = verify_telegram_webapp(x_telegram_init_data)
        return data
    except ValueError as exc:  # invalid or too old initData
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Telegram WebApp auth: {exc}",
        ) from exc
