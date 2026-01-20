from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class DiscountCode(BaseModel):
    code: str
    type: Literal["percentage", "fixed"]
    value: float = Field(..., gt=0)
    isActive: bool = True
    usageLimit: Optional[int] = None
    usedCount: int = 0
    minOrderValue: Optional[float] = None

class DiscountValidateRequest(BaseModel):
    code: str
    orderTotal: float

class DiscountValidateResponse(BaseModel):
    valid: bool
    discountAmount: float = 0.0
    newTotal: float
    message: Optional[str] = None
