from pydantic import BaseModel
from typing import List

class RestaurantModel(BaseModel):
    name: str
    description: str
    image_url: str
    available_slots: List[str]

class BookingModel(BaseModel):
    restaurant_id: str
    customer_name: str
    customer_phone: str
    time_slot: str
    booking_date: str  # format: YYYY-MM-DD

class AdminUser(BaseModel):
    username: str
    password: str