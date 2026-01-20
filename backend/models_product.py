from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float = Field(..., ge=0)
    image: str
    category: str
    variants: List[str]
    stock: Dict[str, int]
    requiresVerification: bool = False
    featured: bool = False
    ageRestricted: bool = False
