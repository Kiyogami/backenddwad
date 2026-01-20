from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from pydantic import BaseModel

from database import db
from models_order import OrderOut
from dependencies import require_admin
from services.telegram_service import send_telegram_message


router = APIRouter(prefix="/api/admin/h2h", tags=["admin-h2h"], dependencies=[Depends(require_admin)])


def _today_range():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def _tomorrow_range():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = start + timedelta(days=1)
    return start, end


@router.get("/verifications", response_model=List[OrderOut])
async def get_verification_queue():
    cursor = db.orders.find(
        {
            "verification.required": True,
            "verification.status": "pending",
        },
        {"_id": 0},
    )
    docs = await cursor.to_list(length=200)
    out: List[OrderOut] = []
    for d in docs:
        d["createdAt"] = datetime.fromisoformat(d["createdAt"])
        d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])
        out.append(OrderOut(**d))
    return out


@router.get("/orders", response_model=List[OrderOut])
async def list_h2h_orders(day: Optional[str] = "today"):
    query = {"delivery.method": "h2h"}

    if day in ("today", "tomorrow"):
        start, end = _today_range() if day == "today" else _tomorrow_range()
        query["createdAt"] = {
            "$gte": start.isoformat(),
            "$lt": end.isoformat(),
        }

    cursor = db.orders.find(query, {"_id": 0})
    docs = await cursor.to_list(length=500)
    out: List[OrderOut] = []
    for d in docs:
        d["createdAt"] = datetime.fromisoformat(d["createdAt"])
        d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])
        out.append(OrderOut(**d))
    return out


class StatusUpdate(BaseModel):
    status: str


class VerificationUpdate(BaseModel):
    verificationStatus: str


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
async def update_order_status(order_id: str, body: StatusUpdate):
    now = datetime.now(timezone.utc)
    doc = await db.orders.find_one_and_update(
        {"id": order_id},
        {
            "$set": {
                "status": body.status,
                "updatedAt": now.isoformat(),
            }
        },
        projection={"_id": 0},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")

    # Powiadom klienta o zmianie statusu
    chat_id = (
        doc.get("customer", {}).get("telegramChatId")
        or doc.get("telegramChatId")
    )
    if chat_id:
        status_map = {
            "ready_for_h2h": "✔️ Twój deal jest gotowy. Ekipa już ogarnięta, lecimy wg slotu.",
            "in_progress_h2h": "🚶‍♂️ H2H w trakcie. Bądź przy spocie, nie znikaj.",
            "completed_h2h": "✅ H2H zaliczone. Dzięki za deal, widzimy się następnym razem.",
            "cancelled": "❌ Zamówienie odwołane. Jak coś, zawsze możesz zamówić od nowa.",
        }
        base = f"🔔 Status zamówienia {doc['id']}:\n"
        extra = status_map.get(body.status, f"Nowy status: {body.status}")
        await send_telegram_message(chat_id, base + extra)

    doc["createdAt"] = datetime.fromisoformat(doc["createdAt"])
    doc["updatedAt"] = now
    return OrderOut(**doc)


@router.patch("/orders/{order_id}/verification", response_model=OrderOut)
async def update_verification_status(order_id: str, body: VerificationUpdate):
    now = datetime.now(timezone.utc)
    doc = await db.orders.find_one_and_update(
        {"id": order_id},
        {
            "$set": {
                "verification.status": body.verificationStatus,
                "updatedAt": now.isoformat(),
            }
        },
        projection={"_id": 0},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")

    chat_id = (
        doc.get("customer", {}).get("telegramChatId")
        or doc.get("telegramChatId")
    )

    if chat_id:
        if body.verificationStatus == "approved":
            txt = (
                f"✅ Weryfikacja do zamówienia {doc['id']} przyklepana.\n"
                "Widzimy się na H2H w ustawionym spocie. Weź tel, hajs i hasło."
            )
            await send_telegram_message(chat_id, txt)
        elif body.verificationStatus == "rejected":
            txt = (
                f"⚠️ Weryfikacja do zamówienia {doc['id']} odrzucona.\n"
                "Nagranie nie siada (słaba jakość / brak numeru / brak twarzy).\n"
                "Nagraj proszę jeszcze raz w WebAppie – twarz, alias i numer zamówienia."
            )
            await send_telegram_message(chat_id, txt)

    doc["createdAt"] = datetime.fromisoformat(doc["createdAt"])
    doc["updatedAt"] = now
    return OrderOut(**doc)
