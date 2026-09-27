# EVE Healthcare — Diagnostic Test Booking API

A production-grade backend service for diagnostic test bookings and simulated payments, built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**.

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Cache | Redis 7 |
| Task Queue | Celery |
| Rate Limiting | SlowAPI |
| Logging | structlog |
| Testing | pytest + httpx (async) |
| Containerization | Docker & Docker Compose |
| Docs | Swagger UI / ReDoc (auto-generated) |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose **OR**
- Python 3.12+, PostgreSQL 16+, Redis 7+

### 🌟 Interactive Web Dashboard (Built-in UI)

The service includes a **real-time single-page web dashboard** served directly by FastAPI at:
- **Dashboard UI**: [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Features of the dashboard:
- 🏥 **Diagnostic Centres & Tests Explorer**: Real-time search, city filters, live test pricing, and one-click test booking.
- 📋 **Patient Booking Management**: Live booking status tracking (`PENDING`, `CONFIRMED`, `FAILED`, `CANCELLED`), instant cancellation.
- 💳 **Simulated Payment Gateway**: Real-time payment simulation with 80% Success / 20% Failed random distribution.
- ⚡ **Webhook Idempotency Lab**: Interactive console to send webhook events, test repeated deliveries, and verify `already_processed` deduplication.
- 👤 **One-Click Demo Auth**: Pre-filled buttons for Demo Patient & Demo Admin.

---

### Pre-loaded Demo Accounts & Seeder

Run the seeder to instantly populate diagnostic centres (Apollo, Metropolis, Dr. Lal PathLabs) and tests:

```bash
python -m app.seed
```
*Or click "Seed Demo Data" directly in the web dashboard!*

| Role | Email | Password |
|---|---|---|
| **Demo Patient** | `patient@evehealthcare.com` | `PatientPass123!` |
| **Demo Admin** | `admin@evehealthcare.com` | `AdminPass123!` |

---

### Option 1: Zero-Setup Local Run (Instant)

Works immediately out of the box with zero external dependencies (uses async SQLite + automatic Postgres fallback):

```bash
# 1. Create and activate virtual environment (Python 3.12 recommended)
py -3.12 -m venv venv
.\venv\Scripts\activate   # On Linux/macOS: source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server (auto-creates database on startup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Open http://localhost:8000 in your browser!
```

### Option 2: Full Docker Stack (PostgreSQL 16 + Redis + Celery)

```bash
# Copy environment file
cp .env.example .env

# Start all 5 services (DB, Redis, API, Celery Worker, Celery Beat)
docker-compose up --build -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Seed initial data
docker-compose exec api python -m app.seed
```

### Option 2: Local Setup

```bash
# Clone and navigate
git clone https://github.com/your-username/eve-healthcare.git
cd eve-healthcare

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local database/redis URLs:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eve_healthcare
# REDIS_URL=redis://localhost:6379/0

# Create the database
createdb eve_healthcare

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/signup` | Register a new user | No |
| POST | `/api/v1/auth/login` | Login and get JWT tokens | No |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |

### Diagnostic Centres & Tests

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/diagnostics/centres` | Create a centre | Admin |
| GET | `/api/v1/diagnostics/centres` | List centres (paginated) | No |
| GET | `/api/v1/diagnostics/centres/{id}` | Get centre details | No |
| PUT | `/api/v1/diagnostics/centres/{id}` | Update a centre | Admin |
| POST | `/api/v1/diagnostics/tests` | Create a diagnostic test | Admin |
| GET | `/api/v1/diagnostics/tests` | List tests (paginated) | No |
| POST | `/api/v1/diagnostics/centres/{id}/tests` | Add test to centre | Admin |
| GET | `/api/v1/diagnostics/centres/{id}/tests` | List centre's tests | No |

### Bookings

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/bookings/` | Create a booking | Yes |
| GET | `/api/v1/bookings/` | List user's bookings (paginated) | Yes |
| GET | `/api/v1/bookings/{id}` | Get booking details | Yes |
| POST | `/api/v1/bookings/{id}/cancel` | Cancel a pending booking | Yes |

### Payments

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/payments/` | Process simulated payment | Yes |
| GET | `/api/v1/payments/{id}` | Get payment details | Yes |
| POST | `/api/v1/payments/webhook/` | Payment webhook (idempotent) | Webhook Secret |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |

---

## Example Requests

### 1. Sign Up

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "phone": "+919876543210"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "SecurePass123!"
  }'
```

### 3. Create a Diagnostic Centre (Admin)

```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/centres \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "name": "Apollo Diagnostics",
    "address": "123 Health Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "phone": "+912212345678"
  }'
```

### 4. Create a Booking

```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{
    "centre_test_id": "<CENTRE_TEST_UUID>",
    "appointment_datetime": "2026-10-01T10:00:00Z"
  }'
```

### 5. Process Payment

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{"booking_id": "<BOOKING_UUID>"}'
```

### 6. Webhook (Payment Status Update)

```bash
curl -X POST http://localhost:8000/api/v1/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{
    "event_id": "evt-abc-123",
    "event_type": "payment.success",
    "transaction_id": "TXN-ABC123",
    "status": "SUCCESS",
    "amount": 500.00,
    "booking_id": "<BOOKING_UUID>"
  }'
```

---

## Database Schema

```
┌──────────────────┐     ┌────────────────────────┐     ┌──────────────────┐
│     users        │     │  diagnostic_centres    │     │ diagnostic_tests │
├──────────────────┤     ├────────────────────────┤     ├──────────────────┤
│ id (PK, UUID)    │     │ id (PK, UUID)          │     │ id (PK, UUID)    │
│ email (unique)   │     │ name                   │     │ name             │
│ full_name        │     │ address                │     │ description      │
│ phone            │     │ city                   │     │ category         │
│ hashed_password  │     │ state                  │     │ created_at       │
│ is_active        │     │ pincode                │     └────────┬─────────┘
│ is_admin         │     │ phone                  │              │
│ created_at       │     │ email                  │              │
│ updated_at       │     │ is_active              │              │
└───────┬──────────┘     │ created_at             │              │
        │                │ updated_at             │              │
        │                └────────────┬───────────┘              │
        │                             │                          │
        │                ┌────────────┴──────────────────────────┤
        │                │       centre_tests                    │
        │                ├──────────────────────────────────────-┤
        │                │ id (PK, UUID)                         │
        │                │ centre_id (FK → diagnostic_centres)   │
        │                │ test_id (FK → diagnostic_tests)       │
        │                │ price (Numeric)                       │
        │                │ is_available                          │
        │                │ created_at                            │
        │                │ UNIQUE(centre_id, test_id)            │
        │                └───────────────┬──────────────────────-┘
        │                                │
┌───────┴────────────────────────────────┴──────┐
│                  bookings                      │
├────────────────────────────────────────────────┤
│ id (PK, UUID)                                  │
│ booking_reference (unique, e.g. EVE-XXXXXXXX)  │
│ user_id (FK → users)                           │
│ centre_test_id (FK → centre_tests)             │
│ appointment_datetime                           │
│ amount (Numeric)                               │
│ status (PENDING|CONFIRMED|FAILED|CANCELLED)    │
│ created_at                                     │
│ updated_at                                     │
└──────────────────────┬─────────────────────────┘
                       │
┌──────────────────────┴─────────────────────────┐
│                  payments                       │
├─────────────────────────────────────────────────┤
│ id (PK, UUID)                                   │
│ booking_id (FK → bookings)                      │
│ transaction_id (unique, e.g. TXN-XXXXXXXXXXXX)  │
│ amount (Numeric)                                │
│ status (PENDING|SUCCESS|FAILED)                 │
│ payment_method                                  │
│ created_at                                      │
│ updated_at                                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              webhook_events                      │
├──────────────────────────────────────────────────┤
│ id (PK, UUID)                                    │
│ event_id (unique — external idempotency key)     │
│ event_type                                       │
│ payload (JSON)                                   │
│ processed (Boolean)                              │
│ processed_at                                     │
│ created_at                                       │
└──────────────────────────────────────────────────┘
```

---

## Architecture & Design Decisions

### Layered Architecture

```
Routers (API Layer) → Services (Business Logic) → Models (Data Layer)
     ↓                      ↓
  Schemas              Exceptions
(Validation)         (Error Handling)
```

- **Routers**: Handle HTTP request/response, validation, and auth
- **Services**: Contain business logic, database queries, and orchestration
- **Models**: Define database schema via SQLAlchemy ORM
- **Schemas**: Pydantic models for request/response validation

### Key Design Decisions

1. **UUID Primary Keys**: Prevent enumeration attacks and enable distributed ID generation
2. **Async Everything**: Full async stack (FastAPI + asyncpg + SQLAlchemy async) for high throughput
3. **Junction Table for Centre-Tests**: A `centre_tests` table with per-centre pricing allows the same test to have different prices at different centres
4. **Webhook Idempotency**: Separate `webhook_events` table tracks processed event IDs to prevent duplicate processing
5. **Booking Reference**: Human-readable reference (`EVE-XXXXXXXX`) for customer communication, separate from internal UUID
6. **Simulated Payments**: 80/20 success/fail ratio for realistic testing
7. **Webhook Secret Verification**: Header-based authentication for webhook security
8. **Soft Booking States**: State machine (PENDING → CONFIRMED/FAILED/CANCELLED) prevents invalid transitions

---

## Important Assumptions

1. A single user creates bookings for themselves (no "book for someone else" flow)
2. Each booking is for exactly one test at one centre
3. The appointment datetime is validated to be in the future
4. Only PENDING bookings can be cancelled
5. Payment amount is derived from the centre_test price at booking time (price lock)
6. Webhook events are authenticated via a shared secret header (`X-Webhook-Secret`)
7. The first admin user should be created manually or via a management script

---

## Running Tests

```bash
# Create test database
createdb eve_healthcare_test

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html -v

# Run specific test file
pytest tests/test_auth.py -v
```

---

## Bonus Features Implemented

- [x] **Redis Caching** — Diagnostic centres list/detail cached with TTL
- [x] **Celery Background Jobs** — Expired booking cleanup, async webhook processing with retries
- [x] **Docker & Docker Compose** — Full containerized setup (API, DB, Redis, Celery worker, Celery beat)
- [x] **Swagger/OpenAPI Documentation** — Auto-generated at `/docs` and `/redoc`
- [x] **Unit/Integration Tests** — Comprehensive test suite with pytest + httpx
- [x] **Structured Logging** — structlog with request ID, method, path, duration
- [x] **Pagination** — Generic paginated response for all list endpoints
- [x] **Rate Limiting** — SlowAPI per-IP rate limiting
- [x] **Retry Handling** — Celery tasks with exponential backoff for webhook processing
- [x] **Request Validation** — Pydantic v2 with custom validators (password strength, phone, future dates)

---

## What I Would Improve With More Time

1. **Refresh Token Rotation** — Store refresh tokens in Redis with revocation support
2. **Role-Based Access Control (RBAC)** — Fine-grained permissions beyond admin/user
3. **Email Notifications** — Send booking confirmation/cancellation emails via Celery
4. **API Versioning** — More robust versioning strategy
5. **Database Connection Pooling** — PgBouncer for production
6. **CI/CD Pipeline** — GitHub Actions for automated testing and deployment
7. **Monitoring** — Prometheus metrics + Grafana dashboards
8. **Audit Logging** — Track all state changes for compliance
9. **Search** — Full-text search for centres and tests
10. **WebSocket** — Real-time booking status updates

---

## Project Structure

```
eve-healthcare/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Environment-based configuration
│   ├── database.py            # Async SQLAlchemy engine & session
│   ├── security.py            # JWT & password hashing utilities
│   ├── dependencies.py        # FastAPI dependencies (auth, DB)
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── diagnostic.py
│   │   ├── booking.py
│   │   └── payment.py
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── diagnostic.py
│   │   ├── booking.py
│   │   └── payment.py
│   ├── routers/               # API route handlers
│   │   ├── auth.py
│   │   ├── diagnostics.py
│   │   ├── bookings.py
│   │   └── payments.py
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   └── cache_service.py
│   ├── middleware/
│   │   └── logging_middleware.py
│   ├── tasks/
│   │   └── celery_app.py      # Celery tasks & configuration
│   └── utils/
│       ├── exceptions.py      # Custom exception classes
│       └── pagination.py      # Generic pagination utilities
├── alembic/                   # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                     # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_diagnostics.py
│   ├── test_bookings.py
│   └── test_payments.py
├── .env.example               # Environment variables template
├── .gitignore
├── .dockerignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## License

This project was built as a backend engineering assignment for EVE Healthcare.
