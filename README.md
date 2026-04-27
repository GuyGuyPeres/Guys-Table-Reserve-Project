# Guy's Table Reserve

A full-stack restaurant table reservation system built with FastAPI and MongoDB. Customers can browse restaurants and book tables; admins manage reservations through a protected dashboard.

---

## Features

**Customer-facing**
- Browse restaurants with images and descriptions
- Multi-step booking flow: pick a date → pick a time slot → enter details
- Guest count selection (1–20)
- Booking confirmation with a unique Booking ID shown after confirming
- Cancel any reservation using the Booking ID + phone number used when booking

**Admin dashboard**
- JWT-protected login
- View all bookings across all restaurants (paginated, 50 per page)
- Copy any Booking ID with one click
- Delete bookings
- Add new restaurants with custom time slots

**Technical**
- Rate limiting: 10 bookings/min and 5 login attempts/min per IP
- MongoDB indexes on `booking_date`, `customer_phone`, and `restaurant_id`
- Full error handling and structured logging on all endpoints
- Input validation on all IDs before database queries

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | MongoDB Atlas (Motor async driver) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Frontend | HTML5, Vanilla JS, CSS3 (no framework) |
| Templating | Jinja2 |

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd RestaurantProject
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root (it is already gitignored):

```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/restaurant_booking?retryWrites=true&w=majority
SECRET_KEY=replace_with_a_long_random_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

> **Tip:** Generate a strong `SECRET_KEY` with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Run the server

```bash
python main.py
```

The app will be available at `http://localhost:8000`.  
The admin dashboard is at `http://localhost:8000/admin`.

On first startup, the default admin account is created automatically using the credentials in `.env`.

---

## API Reference

### Public

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/restaurants` | List all restaurants |
| `POST` | `/api/book` | Create a booking |
| `DELETE` | `/api/bookings/{id}` | Cancel a booking (requires matching phone) |

**POST `/api/book` body:**
```json
{
  "restaurant_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "customer_name": "Guy Peres",
  "customer_phone": "0529918459",
  "time_slot": "19:00",
  "booking_date": "2026-05-10",
  "guest_count": 2
}
```

**DELETE `/api/bookings/{id}` body:**
```json
{ "customer_phone": "0529918459" }
```

### Admin (requires `Authorization: Bearer <token>`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/login` | Get JWT token |
| `GET` | `/api/admin/bookings` | List bookings (paginated) |
| `DELETE` | `/api/admin/bookings/{id}` | Delete a booking |
| `POST` | `/api/admin/restaurants` | Add a new restaurant |

**GET `/api/admin/bookings` query params:**
- `page` (default: 1)
- `limit` (default: 50, max: 200)

---

## Project Structure

```
RestaurantProject/
├── main.py              # FastAPI app, all routes
├── models.py            # Pydantic request/response models
├── auth.py              # JWT creation and verification
├── database.py          # MongoDB connection and collections
├── config.py            # Environment variable loader
├── requirements.txt
├── .env                 # Secrets — never commit this
├── static/
│   ├── script.js        # Customer-facing booking logic
│   └── style.css        # Dark luxury theme
└── templates/
    ├── index.html       # Customer homepage
    └── admin.html       # Admin dashboard
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `SECRET_KEY` | Yes | Secret used to sign JWT tokens |
| `ALGORITHM` | Yes | JWT algorithm (use `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | Token lifetime in minutes |
| `ADMIN_USERNAME` | Yes | Username for the admin account |
| `ADMIN_PASSWORD` | Yes | Password for the admin account |
