import logging
from collections import defaultdict
from time import time as _time
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from bson import ObjectId
from bson.errors import InvalidId
from database import restaurants_collection, bookings_collection, admins_collection
from models import RestaurantModel, BookingModel, CancelBookingRequest, AdminUser
from auth import hash_password, verify_password, create_access_token, get_current_admin
from config import settings
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("restaurant")


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


booking_limiter = RateLimiter(max_calls=10, period=60)
login_limiter = RateLimiter(max_calls=5, period=60)


def to_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid ID format")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env")

    try:
        await bookings_collection.create_index("restaurant_id")
        await bookings_collection.create_index("booking_date")
        await bookings_collection.create_index("customer_phone")
        await restaurants_collection.create_index("name")
        logger.info("Database indexes ensured")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

    try:
        admin_exists = await admins_collection.find_one({"username": settings.ADMIN_USERNAME})
        if not admin_exists:
            await admins_collection.insert_one({
                "username": settings.ADMIN_USERNAME,
                "password": hash_password(settings.ADMIN_PASSWORD)
            })
            logger.info(f"Default admin '{settings.ADMIN_USERNAME}' created")
    except Exception as e:
        logger.error(f"Failed to initialize admin: {e}")
        raise

    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- PUBLIC ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")


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


@app.post("/api/book")
async def book_table(request: Request, booking: BookingModel):
    if not booking_limiter.is_allowed(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute before trying again.")
    try:
        restaurant_oid = to_object_id(booking.restaurant_id)
        result = await restaurants_collection.update_one(
            {"_id": restaurant_oid, "available_slots": booking.time_slot},
            {"$pull": {"available_slots": booking.time_slot}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Time slot already taken or restaurant not found.")

        res_info = await restaurants_collection.find_one({"_id": restaurant_oid})
        booking_data = booking.model_dump()
        booking_data["restaurant_name"] = res_info["name"]

        insert_result = await bookings_collection.insert_one(booking_data)
        booking_id = str(insert_result.inserted_id)
        logger.info(f"Booking {booking_id} created for '{res_info['name']}' on {booking.booking_date}")
        return {"status": "success", "booking_id": booking_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking failed: {e}")
        raise HTTPException(status_code=500, detail="Booking failed. Please try again.")


@app.delete("/api/bookings/{booking_id}")
async def cancel_booking(booking_id: str, data: CancelBookingRequest):
    try:
        oid = to_object_id(booking_id)
        booking = await bookings_collection.find_one({"_id": oid})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found.")
        if booking["customer_phone"] != data.customer_phone:
            raise HTTPException(status_code=403, detail="Phone number does not match this booking.")

        await restaurants_collection.update_one(
            {"_id": to_object_id(booking["restaurant_id"])},
            {"$addToSet": {"available_slots": booking["time_slot"]}}
        )
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
    if not login_limiter.is_allowed(request.client.host):
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
        new_res = await restaurants_collection.insert_one(res.model_dump())
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
