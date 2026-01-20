from fastapi import APIRouter, Depends
from database import db
from models_loyalty import LoyaltyStatus
from dependencies import require_telegram_webapp

router = APIRouter(prefix="/api/loyalty", tags=["loyalty"])

LEVELS = [
    (0, "Początkujący"),
    (100, "Wtajemniczony"),
    (500, "Zaufany Klient"),
    (1000, "VIP"),
    (5000, "Szef"),
    (10000, "Boss")
]

def calculate_level(points: int):
    current_level = LEVELS[0][1]
    next_threshold = LEVELS[1][0]
    
    for i, (threshold, name) in enumerate(LEVELS):
        if points >= threshold:
            current_level = name
            if i + 1 < len(LEVELS):
                next_threshold = LEVELS[i+1][0]
            else:
                next_threshold = points # Max level
    
    return current_level, next_threshold

@router.get("/status", response_model=LoyaltyStatus)
async def get_loyalty_status(tg_data: dict = Depends(require_telegram_webapp)):
    user_id = tg_data.get("user", {}).get("id")
    if not user_id:
        return LoyaltyStatus(points=0, level="Gość", nextLevelThreshold=100, progress=0)
        
    # Aggregate points from orders
    pipeline = [
        {"$match": {"customer.telegramUserId": user_id, "status": {"$in": ["payment_confirmed", "completed", "shipped", "delivered"]}}},
        {"$group": {"_id": None, "totalSpent": {"$sum": "$payment.total"}}}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(length=1)
    total_spent = result[0]["totalSpent"] if result else 0
    
    # 1 point per 1 PLN
    points = int(total_spent)
    
    level, next_threshold = calculate_level(points)
    
    progress = 100
    if next_threshold > points:
        # Simple progress calc for current level bracket could be complex, 
        # let's just do global progress to next threshold
        progress = (points / next_threshold) * 100

    return LoyaltyStatus(
        points=points,
        level=level,
        nextLevelThreshold=next_threshold,
        progress=round(progress, 1)
    )
