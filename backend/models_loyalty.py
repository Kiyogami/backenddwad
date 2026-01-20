from pydantic import BaseModel
from typing import Optional

class UserProfile(BaseModel):
    telegramUserId: int
    telegramUsername: Optional[str] = None
    points: int = 0
    level: str = "Początkujący"
    totalOrders: int = 0
    totalSpent: float = 0.0

class LoyaltyStatus(BaseModel):
    points: int
    level: str
    nextLevelThreshold: int
    progress: float
