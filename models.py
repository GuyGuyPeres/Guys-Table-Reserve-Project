from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List
from datetime import date, timedelta

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

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, v: str) -> str:
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("booking_date must be in YYYY-MM-DD format")
        today = date.today()
        if parsed < today:
            raise ValueError("Booking date cannot be in the past")
        if parsed > today + timedelta(days=90):
            raise ValueError("Booking date cannot be more than 3 months in advance")
        return v

class CancelBookingRequest(BaseModel):
    customer_phone: str

class AdminUser(BaseModel):
    username: str
    password: str