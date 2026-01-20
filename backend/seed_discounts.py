import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

discounts = [
    {"code": "START10", "type": "percentage", "value": 10.0, "isActive": True, "minOrderValue": 50},
    {"code": "VIP20", "type": "percentage", "value": 20.0, "isActive": True, "minOrderValue": 200},
    {"code": "PLN50", "type": "fixed", "value": 50.0, "isActive": True, "minOrderValue": 300},
]

async def seed():
    print("Seeding discounts...")
    mongo_url = os.environ.get('MONGO_URL', "mongodb://localhost:27017")
    db_name = os.environ.get('DB_NAME', "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Upsert discounts
    for d in discounts:
        await db.discounts.update_one(
            {"code": d["code"]}, 
            {"$set": d}, 
            upsert=True
        )
    print("Discounts seeded.")
    client.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
