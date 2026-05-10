from pydantic import BaseModel, EmailStr, Field
from typing import List

class RestaurantModel(BaseModel):
    name: str
    description: str
    image_url: str
    available_slots: List[str]

class BookingModel(BaseModel):
    restaurant_id: str
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    time_slot: str
    booking_date: str  # format: YYYY-MM-DD
    guest_count: int = Field(default=2, ge=1, le=20)

class CancelBookingRequest(BaseModel):
    customer_phone: str

class AdminUser(BaseModel):
    username: str
    password: str