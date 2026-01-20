from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from database import db
from dependencies import require_telegram_webapp
from services.telegram_service import notify_admin_verification_submitted


router = APIRouter(prefix="/api/orders", tags=["verification"])


class SubmitVerificationRequest(BaseModel):
    videoUrl: str


@router.post("/{order_id}/verify")
async def submit_verification(
    order_id: str,
    body: SubmitVerificationRequest,
    tg_data: dict = Depends(require_telegram_webapp)
):
    """Wyślij weryfikację wideo dla zamówienia."""
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization
    user_id = tg_data.get("user", {}).get("id")
    order_user_id = doc.get("customer", {}).get("telegramUserId")
    
    if order_user_id and user_id and order_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update verification
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "verification.videoUrl": body.videoUrl,
                "verification.status": "pending",
                "status": "verification_pending",
                "updatedAt": datetime.now().isoformat()
            }
        }
    )
    
    # Powiadom admina
    customer_name = doc.get("customer", {}).get("name", "Unknown")
    await notify_admin_verification_submitted(order_id, customer_name)
    
    return {"success": True, "message": "Verification submitted"}
