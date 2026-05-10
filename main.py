import logging
from collections import defaultdict
from time import time as _time
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from bson import ObjectId
from bson.errors import InvalidId
from database import restaurants_collection, bookings_collection, admins_collection
from models import RestaurantModel, BookingModel, CancelBookingRequest, AdminUser
from auth import verify_password, create_access_token, get_current_admin
from config import settings
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("restaurant")

DEFAULT_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "18:00", "19:00", "20:00", "21:00", "22:00"]


class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self._calls: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = _time()
        self._calls[key] = [t for t in self._calls[key] if now - t < self.period]
        if len(self._calls[key]) >= self.max_calls:
            return False
        self._calls[key].append(now)
        return True


booking_limiter = RateLimiter(max_calls=3, period=60)
login_limiter = RateLimiter(max_calls=5, period=60)
cancel_limiter = RateLimiter(max_calls=5, period=60)


def to_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid ID format")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.MONGO_URI:
        raise RuntimeError("MONGO_URI must be set in .env")
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in .env")

    try:
        await bookings_collection.create_index("restaurant_id")
        await bookings_collection.create_index("booking_date")
        await bookings_collection.create_index("customer_phone")
        # Compound index to efficiently check for duplicate slot bookings per date
        await bookings_collection.create_index(
            [("restaurant_id", 1), ("booking_date", 1), ("time_slot", 1)],
            unique=True
        )
        await restaurants_collection.create_index("name")
        logger.info("Database indexes ensured")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

    try:
        admin_exists = await admins_collection.find_one({})
        if not admin_exists:
            raise RuntimeError("No admin account found in the database. Add one via MongoDB Compass before starting the app.")
        logger.info("Admin account verified")
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Failed to verify admin: {e}")
        raise

    # Migrate all restaurants to use the standard DEFAULT_SLOTS as their master list
    try:
        result = await restaurants_collection.update_many(
            {},
            {"$set": {"available_slots": DEFAULT_SLOTS}}
        )
        if result.modified_count:
            logger.info(f"Migrated {result.modified_count} restaurant(s) to DEFAULT_SLOTS")
    except Exception as e:
        logger.error(f"Failed to migrate restaurant slots: {e}")

    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


def get_client_ip(request: Request) -> str:
    return request.headers.get("X-Real-IP") or request.client.host


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https: data:; "
            "object-src 'none'; "
            "frame-ancestors 'none'"
        )
        return response


app = FastAPI(lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- PUBLIC ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/restaurants")
async def get_restaurants():
    try:
        restaurants = []
        async for res in restaurants_collection.find():
            res["id"] = str(res["_id"])
            del res["_id"]
            restaurants.append(res)
        return restaurants
    except Exception as e:
        logger.error(f"Failed to fetch restaurants: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurants")


@app.get("/api/restaurants/{restaurant_id}/slots")
async def get_slots_for_date(restaurant_id: str, date: str = Query(..., description="YYYY-MM-DD")):
    """Return available time slots for a specific restaurant and date."""
    try:
        oid = to_object_id(restaurant_id)
        restaurant = await restaurants_collection.find_one({"_id": oid})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")

        master_slots = restaurant.get("available_slots", DEFAULT_SLOTS)

        booked_cursor = bookings_collection.find(
            {"restaurant_id": restaurant_id, "booking_date": date},
            {"time_slot": 1}
        )
        booked_slots = {b["time_slot"] async for b in booked_cursor}

        available = [s for s in master_slots if s not in booked_slots]
        return {"slots": available}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch slots for restaurant {restaurant_id} on {date}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available slots")


@app.post("/api/book")
async def book_table(request: Request, booking: BookingModel):
    if not booking_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute before trying again.")
    try:
        restaurant_oid = to_object_id(booking.restaurant_id)
        restaurant = await restaurants_collection.find_one({"_id": restaurant_oid})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found.")

        master_slots = restaurant.get("available_slots", DEFAULT_SLOTS)
        if booking.time_slot not in master_slots:
            raise HTTPException(status_code=400, detail="Invalid time slot.")

        # Check if this slot is already taken for this restaurant+date
        existing = await bookings_collection.find_one({
            "restaurant_id": booking.restaurant_id,
            "booking_date": booking.booking_date,
            "time_slot": booking.time_slot
        })
        if existing:
            raise HTTPException(status_code=400, detail="Time slot already taken for this date.")

        booking_data = booking.model_dump()
        booking_data["restaurant_name"] = restaurant["name"]

        insert_result = await bookings_collection.insert_one(booking_data)
        booking_id = str(insert_result.inserted_id)
        logger.info(f"Booking {booking_id} created for '{restaurant['name']}' on {booking.booking_date} at {booking.time_slot}")
        return {"status": "success", "booking_id": booking_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking failed: {e}")
        raise HTTPException(status_code=500, detail="Booking failed. Please try again.")


@app.delete("/api/bookings/{booking_id}")
async def cancel_booking(request: Request, booking_id: str, data: CancelBookingRequest):
    if not cancel_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many cancellation attempts. Please wait a minute.")
    try:
        oid = to_object_id(booking_id)
        booking = await bookings_collection.find_one({"_id": oid})
        if not booking or booking["customer_phone"] != data.customer_phone:
            raise HTTPException(status_code=403, detail="Invalid booking ID or phone number.")

        await bookings_collection.delete_one({"_id": oid})
        logger.info(f"Booking {booking_id} cancelled by customer")
        return {"status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancellation failed for {booking_id}: {e}")
        raise HTTPException(status_code=500, detail="Cancellation failed. Please try again.")


# --- ADMIN AUTH ---
@app.post("/api/admin/login")
async def login(request: Request, form_data: AdminUser):
    if not login_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait a minute.")
    try:
        user = await admins_collection.find_one({"username": form_data.username})
        if not user or not verify_password(form_data.password, user["password"]):
            logger.warning(f"Failed login for '{form_data.username}' from {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(data={"sub": user["username"]})
        logger.info(f"Admin '{form_data.username}' logged in")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


# --- ADMIN ROUTES ---
@app.post("/api/admin/restaurants", dependencies=[Depends(get_current_admin)])
async def add_restaurant(res: RestaurantModel):
    try:
        data = res.model_dump()
        # Always use DEFAULT_SLOTS as master regardless of what was submitted
        data["available_slots"] = DEFAULT_SLOTS
        new_res = await restaurants_collection.insert_one(data)
        logger.info(f"Restaurant '{res.name}' added")
        return {"id": str(new_res.inserted_id)}
    except Exception as e:
        logger.error(f"Failed to add restaurant: {e}")
        raise HTTPException(status_code=500, detail="Failed to add restaurant")


@app.get("/api/admin/bookings", dependencies=[Depends(get_current_admin)])
async def get_all_bookings(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    try:
        skip = (page - 1) * limit
        total = await bookings_collection.count_documents({})
        bookings = []
        async for b in bookings_collection.find().skip(skip).limit(limit):
            b["id"] = str(b["_id"])
            del b["_id"]
            bookings.append(b)
        return {
            "bookings": bookings,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": max(1, (total + limit - 1) // limit)
        }
    except Exception as e:
        logger.error(f"Failed to fetch bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


@app.delete("/api/admin/bookings/{booking_id}", dependencies=[Depends(get_current_admin)])
async def delete_booking(booking_id: str):
    try:
        oid = to_object_id(booking_id)
        await bookings_collection.delete_one({"_id": oid})
        logger.info(f"Admin deleted booking {booking_id}")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete booking {booking_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete booking")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
