from fastapi import APIRouter, HTTPException, Depends
from database import db
from models_discount import DiscountCode, DiscountValidateRequest, DiscountValidateResponse
import logging

router = APIRouter(prefix="/api/discounts", tags=["discounts"])
logger = logging.getLogger(__name__)

@router.post("/validate", response_model=DiscountValidateResponse)
async def validate_discount(body: DiscountValidateRequest):
    code = body.code.upper().strip()
    discount = await db.discounts.find_one({"code": code, "isActive": True})
    
    if not discount:
        return DiscountValidateResponse(valid=False, newTotal=body.orderTotal, message="Kod nieprawidłowy lub nieaktywny.")

    # Check limits
    if discount.get("usageLimit") and discount.get("usedCount", 0) >= discount["usageLimit"]:
        return DiscountValidateResponse(valid=False, newTotal=body.orderTotal, message="Limit użycia kodu wyczerpany.")
        
    if discount.get("minOrderValue") and body.orderTotal < discount["minOrderValue"]:
         return DiscountValidateResponse(valid=False, newTotal=body.orderTotal, message=f"Wymagana wartość zamówienia: {discount['minOrderValue']} PLN")

    # Calculate discount
    discount_amount = 0.0
    if discount["type"] == "percentage":
        discount_amount = (discount["value"] / 100) * body.orderTotal
    else:
        discount_amount = discount["value"]

    # Ensure we don't discount more than total
    discount_amount = min(discount_amount, body.orderTotal)
    new_total = body.orderTotal - discount_amount

    return DiscountValidateResponse(
        valid=True,
        discountAmount=round(discount_amount, 2),
        newTotal=round(new_total, 2),
        message="Kod zastosowany pomyślnie!"
    )
