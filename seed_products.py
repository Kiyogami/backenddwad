import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Mock data from frontend
products_data = [
  {
    "id": "1",
    "name": "BUCH Premium",
    "description": "Najwyższej jakości produkt z limitowanej edycji. Ekskluzywna formuła stworzona dla wymagających klientów.",
    "price": 299.99,
    "image": "https://images.unsplash.com/photo-1618215650201-8d552591218d?w=600",
    "category": "premium",
    "variants": ["S", "M", "L", "XL"],
    "stock": { "S": 5, "M": 10, "L": 8, "XL": 3 },
    "requiresVerification": True,
    "featured": True,
    "ageRestricted": False
  },
  {
    "id": "2",
    "name": "MEF Classic",
    "description": "Klasyczna wersja dla koneserów. Sprawdzona receptura w eleganckiej formie.",
    "price": 199.99,
    "image": "https://images.unsplash.com/photo-1618215650454-d03cac422c8f?w=600",
    "category": "classic",
    "variants": ["Standard", "Premium"],
    "stock": { "Standard": 20, "Premium": 8 },
    "requiresVerification": False,
    "featured": True
  },
  {
    "id": "3",
    "name": "KOKO Gold Edition",
    "description": "Złota edycja z limitowanej serii. Wyjątkowy produkt dla wyjątkowych osób.",
    "price": 449.99,
    "image": "https://images.unsplash.com/photo-1760804876166-aae5861ec7c1?w=600",
    "category": "limited",
    "variants": ["Gold", "Platinum"],
    "stock": { "Gold": 3, "Platinum": 2 },
    "requiresVerification": True,
    "featured": True
  },
  {
    "id": "4",
    "name": "PIGULY Set",
    "description": "Kompletny zestaw w eleganckim opakowaniu. Idealny na prezent.",
    "price": 349.99,
    "image": "https://images.unsplash.com/photo-1760804876134-a8089aaeccca?w=600",
    "category": "sets",
    "variants": ["3-Pack", "5-Pack", "10-Pack"],
    "stock": { "3-Pack": 15, "5-Pack": 10, "10-Pack": 5 },
    "requiresVerification": False,
    "featured": False
  },
  {
    "id": "5",
    "name": "BUCH Elite",
    "description": "Najwyższa półka w naszej ofercie. Dla prawdziwych znawców.",
    "price": 599.99,
    "image": "https://images.unsplash.com/photo-1702882239258-ab876240f95c?w=600",
    "category": "elite",
    "variants": ["Elite", "Supreme"],
    "stock": { "Elite": 4, "Supreme": 2 },
    "requiresVerification": True,
    "featured": True
  },
  {
    "id": "6",
    "name": "MEF Starter",
    "description": "Idealny produkt na początek przygody. Doskonała jakość w przystępnej cenie.",
    "price": 149.99,
    "image": "https://images.unsplash.com/photo-1618215649907-b51d8accb1ec?w=600",
    "category": "starter",
    "variants": ["Starter", "Starter+"],
    "stock": { "Starter": 30, "Starter+": 20 },
    "requiresVerification": False,
    "featured": False,
    "ageRestricted": False
  },
  {
    "id": "7",
    "name": "Xanax 2mg",
    "description": "Mocny preparat na uspokojenie. Tylko dla pełnoletnich klientów (18+).",
    "price": 249.99,
    "image": "https://images.unsplash.com/photo-1587855209276-89dabc0d2c00?w=600",
    "category": "leki",
    "variants": ["Blister 10 szt.", "Blister 30 szt."],
    "stock": { "Blister 10 szt.": 20, "Blister 30 szt.": 10 },
    "requiresVerification": True,
    "featured": True,
    "ageRestricted": True
  },
  {
    "id": "8",
    "name": "Oxy 80mg",
    "description": "Silny preparat przeciwbólowy. Wymaga pełnoletności i weryfikacji tożsamości.",
    "price": 399.99,
    "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600",
    "category": "leki",
    "variants": ["Blister 10 szt.", "Blister 20 szt."],
    "stock": { "Blister 10 szt.": 15, "Blister 20 szt.": 8 },
    "requiresVerification": True,
    "featured": False,
    "ageRestricted": True
  }
]

async def seed():
    print("Seeding database...")
    mongo_url = os.environ.get('MONGO_URL', "mongodb://localhost:27017")
    db_name = os.environ.get('DB_NAME', "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Check if products exist
    count = await db.products.count_documents({})
    if count > 0:
        print(f"Products collection already has {count} items. Skipping seed.")
    else:
        await db.products.insert_many(products_data)
        print("Inserted products.")
        
    client.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
