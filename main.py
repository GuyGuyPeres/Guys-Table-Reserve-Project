from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from bson import ObjectId
from database import restaurants_collection, bookings_collection, admins_collection
from models import RestaurantModel, BookingModel, AdminUser
from auth import hash_password, verify_password, create_access_token, get_current_admin
from contextlib import asynccontextmanager
import uvicorn

# Modern Lifespan pattern (replaces @app.on_event("startup"))
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create a default admin if none exists
    admin_exists = await admins_collection.find_one({"username": "admin"})
    if not admin_exists:
        await admins_collection.insert_one({
            "username": "admin",
            "password": hash_password("admin123")
        })
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- PUBLIC ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # FIX: Pass request as a keyword argument
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/restaurants")
async def get_restaurants():
    restaurants = []
    async for res in restaurants_collection.find():
        res["id"] = str(res["_id"])
        del res["_id"]
        restaurants.append(res)
    return restaurants

@app.post("/api/book")
async def book_table(booking: BookingModel):
    result = await restaurants_collection.update_one(
        {"_id": ObjectId(booking.restaurant_id), "available_slots": booking.time_slot},
        {"$pull": {"available_slots": booking.time_slot}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Time slot already taken or restaurant not found.")
    
    # FIX: Use model_dump() instead of dict() for Pydantic v2
    booking_data = booking.model_dump()
    res_info = await restaurants_collection.find_one({"_id": ObjectId(booking.restaurant_id)})
    booking_data["restaurant_name"] = res_info["name"]
    
    await bookings_collection.insert_one(booking_data)
    return {"status": "success"}

# --- ADMIN AUTH ---
@app.post("/api/admin/login")
async def login(form_data: AdminUser):
    # Search for the user in the database
    user = await admins_collection.find_one({"username": form_data.username})
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

# --- ADMIN DASHBOARD ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.post("/api/admin/restaurants", dependencies=[Depends(get_current_admin)])
async def add_restaurant(res: RestaurantModel):
    # FIX: Use model_dump() instead of dict()
    new_res = await restaurants_collection.insert_one(res.model_dump())
    return {"id": str(new_res.inserted_id)}

@app.get("/api/admin/bookings", dependencies=[Depends(get_current_admin)])
async def get_all_bookings():
    bookings = []
    async for b in bookings_collection.find():
        b["id"] = str(b["_id"])
        del b["_id"]
        bookings.append(b)
    return bookings

@app.delete("/api/admin/bookings/{booking_id}", dependencies=[Depends(get_current_admin)])
async def delete_booking(booking_id: str):
    await bookings_collection.delete_one({"_id": ObjectId(booking_id)})
    return {"status": "deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)