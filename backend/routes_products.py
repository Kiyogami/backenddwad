from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import db
from models_product import Product

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("", response_model=List[Product])
async def get_products():
    """Fetch all products from the database."""
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    return products

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Fetch a single product by ID."""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
