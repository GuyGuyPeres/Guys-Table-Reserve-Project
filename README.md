<div align="center">

![Banner](https://placehold.co/900x200/0c0d0f/c9a84c?text=Guy%27s+Table+Reserve&font=montserrat)

# 🍽️ Guy's Table Reserve

### A sleek, full-stack restaurant reservation system — book a table in seconds, manage everything from one dashboard.

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
| Frontend | HTML5, Vanilla JS, CSS3 | — |
| Environment | python-dotenv | 1.2.2 |

---

## ✨ Key Features

- **Multi-step booking flow** — Customers select a date, pick an available time slot, enter their details and guest count, all in a clean modal without leaving the page.
- **Booking ID + self-cancellation** — Every confirmed reservation returns a unique Booking ID. Customers can cancel at any time using their ID and phone number — no account required.
- **JWT-protected admin dashboard** — Admins log in with credentials from `.env`; all management endpoints require a signed token, verified on every request.
- **Paginated reservations table** — Admin bookings load 50 per page with Prev/Next controls and a one-click copy button for each Booking ID.
- **Rate limiting** — Booking endpoint is capped at 10 requests/min per IP; login at 5/min — built-in, no external dependency required.
- **MongoDB indexes** — Indexes on `booking_date`, `customer_phone`, and `restaurant_id` are created at startup so queries stay fast as the database grows.
- **Full error handling** — Every route wraps MongoDB operations in try/except; invalid ObjectIds are caught before hitting the database; all errors return structured JSON.
- **Structured logging** — Timestamped log lines for every key event: startup, new bookings, admin logins, failed attempts, and errors.
- **Time slot integrity** — Slots are atomically pulled from the restaurant document on booking and restored on cancellation, preventing double-bookings.

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [MongoDB Atlas account](https://www.mongodb.com/cloud/atlas) (free tier works fine)
- A terminal / command prompt

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CaptainPeres/RestaurantProject.git
   cd RestaurantProject
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

- **`ServerSelectionTimeoutError`** — Check your `MONGO_URI`. Make sure your IP is whitelisted in MongoDB Atlas under Network Access.
- **`ModuleNotFoundError`** — Make sure your virtual environment is activated before running `pip install`.
- **`RuntimeError: ADMIN_USERNAME and ADMIN_PASSWORD must be set`** — Your `.env` file is missing or not being loaded. Confirm the file is in the project root (same folder as `main.py`).
- **Port already in use** — Another process is on port 8000. Stop it or change the port in `main.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`.

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
| `GET` | `/api/restaurants` | — | List all restaurants |
| `POST` | `/api/book` | — | Create a booking |
| `DELETE` | `/api/bookings/{id}` | — | Cancel a booking (phone verification) |
| `POST` | `/api/admin/login` | — | Get a JWT token |
| `GET` | `/api/admin/bookings` | Bearer token | List bookings (paginated) |
| `DELETE` | `/api/admin/bookings/{id}` | Bearer token | Delete a booking |
| `POST` | `/api/admin/restaurants` | Bearer token | Add a new restaurant |

---

### POST `/api/book`

```bash
curl -X POST http://localhost:8000/api/book \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "customer_name": "Guy Peres",
    "customer_phone": "0529918459",
    "time_slot": "19:00",
    "booking_date": "2026-05-10",
    "guest_count": 2
  }'
```

**Response** `201`
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
  -d '{ "customer_phone": "0529918459" }'
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
curl http://localhost:8000/api/admin/bookings?page=1&limit=50 \
  -H "Authorization: Bearer <token>"
```

**Response** `200`
```json
{
  "bookings": [ { "id": "...", "restaurant_name": "...", "customer_name": "...", "booking_date": "2026-05-10", "time_slot": "19:00", "guest_count": 2 } ],
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
| `400` | Bad request (slot taken, invalid ID format) |
| `401` | Invalid or missing credentials |
| `403` | Phone number does not match booking |
| `404` | Booking not found |
| `429` | Rate limit exceeded |
| `500` | Internal server error (logged server-side) |

---

## 🏗 Architecture

### Folder Structure

```text
📁 RestaurantProject/
├── 📄 main.py            # FastAPI app — all routes, rate limiter, lifespan
├── 📄 models.py          # Pydantic models (BookingModel, RestaurantModel, etc.)
├── 📄 auth.py            # JWT creation & verification, bcrypt helpers
├── 📄 database.py        # MongoDB client + collection handles
├── 📄 config.py          # Loads all env vars via python-dotenv
├── 📄 requirements.txt
├── 📄 .env               # Secrets — never commit ⚠️
├── 📁 static/
│   ├── 📄 script.js      # Booking flow, cancellation, toast notifications
│   └── 📄 style.css      # Dark luxury theme (CSS variables, animations)
└── 📁 templates/
    ├── 📄 index.html     # Customer homepage — restaurant grid + booking modal
    └── 📄 admin.html     # Admin dashboard — login, bookings table, add restaurant
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
     ▼
MongoDB Atlas
     │
     ▼
JSON Response  ◄── Exception Handler ◄── try/except (500 on DB failure)
```

---


<div align="center">

Made with ☕ and some hours in class.

⭐ **If this project helped you, consider giving it a star!** ⭐

Built with 💻 by [CaptainPeres](https://github.com/GuyGuyPeres)

</div>
