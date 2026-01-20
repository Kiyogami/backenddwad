from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database import db
from models_order import OrderOut
from services.telegram_service import send_order_status_update


router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


class UpdateOrderStatusRequest(BaseModel):
    status: str
    trackingNumber: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=List[OrderOut])
async def list_all_orders(
    status_filter: Optional[str] = None,
    delivery_filter: Optional[str] = None,
    limit: int = 100
):
    """Lista wszystkich zamówień (admin)."""
    query = {}
    
    if status_filter:
        query["status"] = status_filter
    
    if delivery_filter:
        query["delivery.method"] = delivery_filter
    
    cursor = db.orders.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit)
    
    docs = await cursor.to_list(length=limit)
    out: List[OrderOut] = []
    for d in docs:
        d["createdAt"] = datetime.fromisoformat(d["createdAt"])
        d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])
        out.append(OrderOut(**d))
    return out


@router.get("/{order_id}", response_model=OrderOut)
async def get_order_details(order_id: str):
    """Pobierz szczegóły zamówienia (admin)."""
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    
    doc["createdAt"] = datetime.fromisoformat(doc["createdAt"])
    doc["updatedAt"] = datetime.fromisoformat(doc["updatedAt"])
    return OrderOut(**doc)


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, body: UpdateOrderStatusRequest):
    """Aktualizuj status zamówienia i wyślij powiadomienie."""
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Aktualizuj status
    update_data = {
        "status": body.status,
        "updatedAt": datetime.now().isoformat()
    }
    
    if body.trackingNumber:
        update_data["delivery.trackingNumber"] = body.trackingNumber
    
    if body.notes:
        update_data["notes"] = body.notes
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    # Wyślij powiadomienie do klienta
    customer = doc.get("customer", {})
    chat_id = customer.get("telegramChatId") or customer.get("telegramUserId")
    
    if chat_id:
        await send_order_status_update(
            order_id=order_id,
            chat_id=chat_id,
            status=body.status,
            tracking_number=body.trackingNumber
        )
    
    return {"success": True, "message": "Status zaktualizowany"}


@router.get("/stats/summary")
async def get_order_stats():
    """Statystyki zamówień."""
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total": {"$sum": "$payment.total"}
            }
        }
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(None)
    
    stats = {
        "byStatus": {},
        "totalOrders": 0,
        "totalRevenue": 0
    }
    
    for item in result:
        status_name = item["_id"]
        stats["byStatus"][status_name] = {
            "count": item["count"],
            "total": item["total"]
        }
        stats["totalOrders"] += item["count"]
        stats["totalRevenue"] += item["total"]
    
    return stats
