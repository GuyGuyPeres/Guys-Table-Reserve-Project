from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client.restaurant_booking

# Collections
restaurants_collection = db.get_collection("restaurants")
bookings_collection = db.get_collection("bookings")
admins_collection = db.get_collection("admins")