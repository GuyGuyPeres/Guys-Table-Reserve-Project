<div align="center">

![Banner](https://placehold.co/900x200/0c0d0f/c9a84c?text=Guy%27s+Table+Reserve&font=montserrat)

# 🍽️ Guy's Table Reserve

### A sleek, full-stack restaurant reservation system - book a table in seconds, manage everything from one dashboard.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-black?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-c9a84c?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)

</div>

---

## 📖 Table of Contents
- [Tech Stack](#-tech-stack)
- [Key Features](#-key-features)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Contributing](#-contributing)

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.136.1 |
| ASGI Server | Uvicorn | 0.46.0 |
| Database | MongoDB Atlas (Motor async driver) | Motor 3.7.1 |
| Authentication | JWT (python-jose) + bcrypt (passlib) | jose 3.5.0 |
| Data Validation | Pydantic | 2.13.3 |
| Templating | Jinja2 | 3.1.6 |
| Frontend | HTML5, Vanilla JS, CSS3 | - |
| Environment | python-dotenv | 1.2.2 |

---

## ✨ Key Features

- **Multi-step booking flow** - Customers pick a date, select an available time slot for that specific date, fill in their details and guest count - all inside a clean modal without leaving the page.
- **Date-aware slot availability** - Available time slots are computed live per date (`master slots − already booked for that day`), so booking "19:00 on Monday" never blocks "19:00 on Tuesday". A dedicated `/api/restaurants/{id}/slots?date=` endpoint serves each date's real-time availability.
- **Booking confirmation popup** - After a successful booking, a styled in-site modal displays the full reservation summary (restaurant, name, phone, date, time, guests, and Booking ID) with a one-click copy button - no native browser dialogs.
- **Booking ID + self-cancellation** - Every confirmed reservation returns a unique Booking ID. Customers can cancel any time using their ID and phone number - no account required.
- **JWT-protected admin dashboard** - Admins log in with credentials from `.env`; all management endpoints require a signed token verified on every request. SVG icons in the sidebar for a clean, consistent look.
- **Paginated reservations table** - Admin bookings load 50 per page with Prev/Next controls and a one-click copy button for each Booking ID (shows `✓ Copied` feedback for 1.5 s).
- **Rate limiting** - Booking endpoint capped at 10 requests/min per IP; login at 5/min - custom in-memory implementation, no external dependency.
- **MongoDB indexes** - Indexes on `booking_date`, `customer_phone`, `restaurant_id`, and a unique compound index on `(restaurant_id, booking_date, time_slot)` prevent double-bookings at the database level and keep queries fast.
- **Full error handling & logging** - Every route wraps MongoDB operations in try/except; invalid ObjectIds are caught before hitting the database; all errors return structured JSON; key events are timestamped in the server log.
- **SVG favicon** - A fork-and-knife SVG icon displays sharp at any size across all modern browsers.

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [MongoDB Atlas account](https://www.mongodb.com/cloud/atlas) (free tier works fine)
- A terminal / command prompt

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GuyGuyPeres/Guys-Table-Reserve-Project.git
   cd Guys-Table-Reserve-Project
   ```

2. **Create and activate a virtual environment**
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   MONGO_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/restaurant_booking?retryWrites=true&w=majority
   SECRET_KEY=replace_with_a_long_random_string
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_secure_password
   ```

   > ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

   Generate a strong `SECRET_KEY` with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

<details>
<summary>🔧 <strong>Troubleshooting</strong></summary>

- **`ServerSelectionTimeoutError`** - Check your `MONGO_URI`. Make sure your IP is whitelisted in MongoDB Atlas under Network Access.
- **`ModuleNotFoundError`** - Make sure your virtual environment is activated before running `pip install`.
- **`RuntimeError: ADMIN_USERNAME and ADMIN_PASSWORD must be set`** - Your `.env` file is missing or not being loaded. Confirm the file is in the project root (same folder as `main.py`).
- **Port already in use** - Another process is on port 8000. Stop it or change the port in `main.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`.

</details>

### Run the App

```bash
python main.py
```

App runs at → **http://localhost:8000**  
Admin dashboard → **http://localhost:8000/admin**

---

## 💡 Usage

All API endpoints are served at `http://localhost:8000`. Request and response bodies use `application/json`.

### Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/restaurants` | - | List all restaurants |
| `GET` | `/api/restaurants/{id}/slots?date=` | - | Available time slots for a specific date |
| `POST` | `/api/book` | - | Create a booking |
| `DELETE` | `/api/bookings/{id}` | - | Cancel a booking (phone verification) |
| `POST` | `/api/admin/login` | - | Get a JWT token |
| `GET` | `/api/admin/bookings` | Bearer token | List bookings (paginated) |
| `DELETE` | `/api/admin/bookings/{id}` | Bearer token | Delete a booking |
| `POST` | `/api/admin/restaurants` | Bearer token | Add a new restaurant |

---

### GET `/api/restaurants/{id}/slots`

Returns available (not yet booked) time slots for a restaurant on a specific date.

```bash
curl "http://localhost:8000/api/restaurants/64f1a2b3c4d5e6f7a8b9c0d1/slots?date=2026-05-10"
```

**Response** `200`
```json
{ "slots": ["10:00", "11:00", "13:00", "18:00", "20:00", "21:00", "22:00"] }
```

---

### POST `/api/book`

```bash
curl -X POST http://localhost:8000/api/book \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "customer_name": "Guy Peres",
    "customer_phone": "0500000000",
    "time_slot": "19:00",
    "booking_date": "2026-05-10",
    "guest_count": 2
  }'
```

**Response** `200`
```json
{
  "status": "success",
  "booking_id": "6650fa3e2b1c4a0012abcdef"
}
```

---

### DELETE `/api/bookings/{booking_id}`

```bash
curl -X DELETE http://localhost:8000/api/bookings/6650fa3e2b1c4a0012abcdef \
  -H "Content-Type: application/json" \
  -d '{ "customer_phone": "0500000000" }'
```

**Response** `200`
```json
{ "status": "cancelled" }
```

---

### POST `/api/admin/login`

```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{ "username": "admin", "password": "your_secure_password" }'
```

**Response** `200`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### GET `/api/admin/bookings`

```bash
curl "http://localhost:8000/api/admin/bookings?page=1&limit=50" \
  -H "Authorization: Bearer <token>"
```

**Response** `200`
```json
{
  "bookings": [
    {
      "id": "6650fa3e2b1c4a0012abcdef",
      "restaurant_name": "Le Jardin",
      "customer_name": "Guy Peres",
      "customer_phone": "0500000000",
      "booking_date": "2026-05-10",
      "time_slot": "19:00",
      "guest_count": 2
    }
  ],
  "total": 120,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

---

### Error Responses

All errors return this shape:
```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request (slot already taken for that date, invalid ID format) |
| `401` | Invalid or missing credentials |
| `403` | Phone number does not match booking |
| `404` | Restaurant or booking not found |
| `429` | Rate limit exceeded |
| `500` | Internal server error (logged server-side) |

---

## 🏗 Architecture

### Folder Structure

```text
📁 RestaurantProject/
├── 📄 main.py            # FastAPI app - routes, rate limiter, lifespan, DEFAULT_SLOTS
├── 📄 models.py          # Pydantic models (BookingModel, RestaurantModel, etc.)
├── 📄 auth.py            # JWT creation & verification, bcrypt helpers
├── 📄 database.py        # MongoDB client + collection handles
├── 📄 config.py          # Loads all env vars via python-dotenv
├── 📄 requirements.txt
├── 📄 .env               # Secrets - never commit ⚠️
├── 📁 static/
│   ├── 📄 script.js      # Booking flow, confirmation modal, cancellation, toasts
│   ├── 📄 style.css      # Dark luxury theme (CSS variables, animations, modals)
│   └── 📄 favicon.svg    # Fork-and-knife SVG icon
└── 📁 templates/
    ├── 📄 index.html     # Customer page - restaurant grid, booking modal, confirmation popup, cancel section
    └── 📄 admin.html     # Admin dashboard - login, bookings table, add restaurant
```

### Request Flow

```
HTTP Request
     │
     ▼
FastAPI Router (main.py)
     │
     ├─ RateLimiter.is_allowed(ip) ──✗──► 429 Too Many Requests
     │
     ├─ Pydantic validation ──────────✗──► 422 Unprocessable Entity
     │
     ├─ to_object_id() ──────────────✗──► 400 Invalid ID
     │
     ├─ JWT Auth / get_current_admin ─✗──► 401 Unauthorized
     │
     ▼
Motor (async MongoDB driver)
     │
     ├─ /slots?date=   → master_slots − booked_slots_for_date
     │
     ├─ POST /book     → check duplicate (restaurant+date+slot), then insert
     │
     └─ DELETE /book   → verify phone, delete booking (slot auto-restores)
     │
     ▼
MongoDB Atlas
     │
     ▼
JSON Response  ◄── Exception Handler ◄── try/except (500 on DB failure)
```

### Slot Availability Model

Time slots are **not** stored as mutable state on the restaurant document. Instead:

- `available_slots` on each restaurant is a fixed master list (`10:00 → 14:00`, `18:00 → 22:00`)
- When a date is selected in the UI, the frontend fetches `/api/restaurants/{id}/slots?date=YYYY-MM-DD`
- The backend computes: **available = master_slots − slots with existing bookings for that date**
- A unique compound index on `(restaurant_id, booking_date, time_slot)` enforces no duplicates at the DB level

---

<div align="center">

Made with ☕ and some hours in class.

⭐ **If this project helped you, consider giving it a star!** ⭐

Built with 💻 by [Guy Peres](https://github.com/GuyGuyPeres/Guys-Table-Reserve-Project)

</div>