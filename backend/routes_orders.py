from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
import uuid

from database import db
from models_order import OrderIn, OrderOut
from dependencies import require_telegram_webapp
from services.telegram_service import (
    send_order_confirmation,
    send_order_status_update,
    notify_admin_new_order
)


router = APIRouter(prefix="/api/orders", tags=["orders"])


def generate_order_id() -> str:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"ORD-{stamp}-{short}"


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderIn,
    tg_data: dict = Depends(require_telegram_webapp),  # validate Telegram WebApp initData
):
    """Tworzenie zamówienia z WebAppa.

    Wymagana poprawna nagłówkowa autoryzacja Telegram WebApp przez X-Telegram-Init-Data.
    """
    now = datetime.now(timezone.utc)
    order_id = generate_order_id()
    
    # Extract user info from tg_data to ensure customer mapping is correct/verified
    user = tg_data.get("user", {})
    user_id = user.get("id")
    username = user.get("username")
    
    # Optional: Force override customer telegram ID with authenticated one
    if user_id:
        body.customer.telegramUserId = user_id
    if username:
        body.customer.telegramUsername = username

    # Weryfikacja: wideo wymagane tylko dla H2H
    requires_verification = body.delivery.method == "h2h"

    doc = {
        "id": order_id,
        "customer": body.customer.model_dump(),
        "items": [i.model_dump() for i in body.items],
        "delivery": body.delivery.model_dump(),
        "payment": body.payment.model_dump(),
        "verification": {
            **body.verification.model_dump(),
            "required": requires_verification,
            "status": "pending" if requires_verification else body.verification.status,
        },
        "status": "verification_pending" if requires_verification else "payment_confirmed",
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

    await db.orders.insert_one(doc)

    # Wyślij powiadomienia
    chat_id = body.customer.telegramChatId or user_id
    if chat_id:
        await send_order_confirmation(
            order_id=order_id,
            chat_id=chat_id,
            customer_name=body.customer.name,
            total=body.payment.total
        )
    
    # Powiadom admina
    await notify_admin_new_order(
        order_id=order_id,
        customer_name=body.customer.name,
        total=body.payment.total,
        delivery_method=body.delivery.method
    )

    # Przygotuj dane do odpowiedzi (konwersja timestampów na datetime)
    out_doc = {
        **doc,
        "createdAt": now,
        "updatedAt": now,
    }
    return OrderOut(**out_doc)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    tg_data: dict = Depends(require_telegram_webapp)
):
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Check if user owns the order (security check)
    user_id = tg_data.get("user", {}).get("id")
    order_user_id = doc.get("customer", {}).get("telegramUserId")
    
    # If user_id is present and matches, or if strict check is needed
    # For now, if order has telegramUserId, it must match.
    if order_user_id and user_id and order_user_id != user_id:
         raise HTTPException(status_code=403, detail="Not authorized to view this order")

    doc["createdAt"] = datetime.fromisoformat(doc["createdAt"])
    doc["updatedAt"] = datetime.fromisoformat(doc["updatedAt"])
    return OrderOut(**doc)


@router.get("", response_model=List[OrderOut])
async def list_orders(
    tg_data: dict = Depends(require_telegram_webapp)
):
    """List orders for the authenticated Telegram user."""
    user_id = tg_data.get("user", {}).get("id")
    
    if not user_id:
        # Should not happen if require_telegram_webapp passes, but just in case
        return []

    # Filter by telegramUserId
    cursor = db.orders.find(
        {"customer.telegramUserId": user_id}, 
        {"_id": 0}
    ).sort("createdAt", -1)
    
    docs = await cursor.to_list(length=200)
    out: List[OrderOut] = []
    for d in docs:
        d["createdAt"] = datetime.fromisoformat(d["createdAt"])
        d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])
        out.append(OrderOut(**d))
    return out
