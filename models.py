from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List
from datetime import date, timedelta

class RestaurantModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500)
    image_url: str = Field(max_length=500)
    available_slots: List[str]

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("image_url must be a valid HTTP or HTTPS URL")
        return v

class BookingModel(BaseModel):
    restaurant_id: str = Field(min_length=1, max_length=24)
    customer_name: str = Field(min_length=1, max_length=100)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=5, max_length=30)
    time_slot: str = Field(min_length=1, max_length=10)
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