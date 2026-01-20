from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime


class OrderItem(BaseModel):
    productId: str
    name: str
    variant: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unitPrice: float = Field(..., ge=0)
    totalPrice: float = Field(..., ge=0)


class Customer(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    telegramUserId: Optional[int] = None
    telegramChatId: Optional[int] = None
    telegramUsername: Optional[str] = None


class DeliveryInfo(BaseModel):
    method: Literal["h2h", "inpost", "drop"]
    lockerCode: Optional[str] = None
    pickupLocation: Optional[str] = None
    pickupTimeSlot: Optional[str] = None
    pickupAlias: Optional[str] = None


class PaymentInfo(BaseModel):
    method: Literal["blik", "stripe", "przelewy24", "cod", "telegram"]
    status: Literal["pending", "confirmed", "failed"] = "pending"
    paymentId: Optional[str] = None
    currency: str = "PLN"
    subtotal: float = Field(..., ge=0)
    deliveryCost: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    discountCode: Optional[str] = None
    discountAmount: float = 0.0


class VerificationInfo(BaseModel):
    required: bool = False
    status: Optional[Literal["pending", "approved", "rejected", "skipped"]] = None
    videoUrl: Optional[str] = None
    notes: Optional[str] = None


class OrderBase(BaseModel):
    customer: Customer
    items: List[OrderItem]
    delivery: DeliveryInfo
    payment: PaymentInfo
    verification: VerificationInfo


class OrderIn(OrderBase):
    """Wejście z frontu (checkout). Bez pól systemowych."""
    pass


class OrderOut(OrderBase):
    """Wyjście na front / admina."""
    id: str
    status: str
    createdAt: datetime
    updatedAt: datetime
