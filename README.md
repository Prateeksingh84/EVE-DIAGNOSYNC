<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0e1a,20:0d2137,40:0a3d62,60:1a5276,80:0d2137,100:0a0e1a&height=220&section=header&text=Eve%20DiagnoSync&fontSize=50&fontColor=00BFFF&fontAlignY=38&desc=Diagnostic%20Booking%20%26%20Settlement%20Platform&descAlignY=56&descSize=18&descColor=ffffff&animation=fadeIn" />

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=18&pause=900&color=22D3EE&center=true&vCenter=true&width=750&lines=FastAPI+%7C+SQLAlchemy+2.0+%7C+PostgreSQL+%7C+Redis+%7C+Celery;Async+Booking+Engine+with+Slot+Capacity+Guards;Idempotent+Webhooks+%2B+HMAC+Verification;Rotating+JWT+Auth+%2B+Family+Token+Tracking;PDF+Medical+Receipts+%2B+Analytics+Engine)](https://git.io/typing-svg)

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-Task_Queue-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)

</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

<div align="center">
<h2>⚡ What Makes This Production-Grade</h2>
</div>

```python
#!/usr/bin/env python3
# ================================================================
#   eve_diagnosync.py  -  Distributed Diagnostic Platform
# ================================================================

class EveDiagnoSync:

    name        = "Eve DiagnoSync"
    type        = "Distributed Diagnostic Booking & Settlement Platform"
    stack       = ["FastAPI", "SQLAlchemy 2.0", "PostgreSQL 16",
                   "Redis 7", "Celery", "ReportLab", "slowapi"]

    highlights  = {
        "Booking Engine"  : "Async slot reservations with capacity guards & race condition mitigation",
        "Payments"        : "Idempotent webhook processor with deduplication tables + HMAC verification",
        "Auth Pipeline"   : "Rotating JWT refresh-token with family tracking & token hijack mitigation",
        "PDF Engine"      : "Automated in-memory medical receipt generator via ReportLab",
        "Analytics"       : "Executive BI engine with revenue KPIs, conversion rates & CSV export",
        "Architecture"    : "Fully async stack: FastAPI + asyncpg + SQLAlchemy async for high throughput",
    }

    demo_accounts = {
        "patient" : {"email": "patient@evehealthcare.com", "password": "PatientPass123!"},
        "admin"   : {"email": "admin@evehealthcare.com",   "password": "AdminPass123!"},
    }
```

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🛠️ Tech Stack

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

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🌟 Interactive Web Dashboard

The service ships a **real-time single-page dashboard** served directly by FastAPI:

| URL | Purpose |
|---|---|
| `http://localhost:8000/` | Main Dashboard UI |
| `http://localhost:8000/dashboard` | Dashboard (alternate) |
| `http://localhost:8000/docs` | Interactive Swagger Docs |
| `http://localhost:8000/redoc` | ReDoc Documentation |

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🏥 Core Booking Features</h4>
      <ul>
        <li>Diagnostic Centres & Tests Explorer with real-time search and city filters</li>
        <li>Conflict Prevention & Slot Capacity (30-min intervals, max 5 concurrent)</li>
        <li>Live booking status tracking (PENDING, CONFIRMED, FAILED, CANCELLED)</li>
        <li>Instant cancellation from dashboard</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>💳 Payments & Analytics</h4>
      <ul>
        <li>Simulated Payment Gateway (80% success / 20% fail distribution)</li>
        <li>Hospital-grade PDF invoices with preparation guidelines</li>
        <li>Executive Admin BI: Revenue KPIs, conversion rates, CSV export</li>
        <li>Webhook Idempotency Lab with already_processed deduplication</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4>🔐 Auth & Security</h4>
      <ul>
        <li>Stateful Refresh Token Rotation with zero-replay-attack demo</li>
        <li>Family revocation on token hijack detection</li>
        <li>HMAC webhook secret verification</li>
        <li>One-click Demo Auth buttons (Patient & Admin)</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>📧 Notifications & Audit</h4>
      <ul>
        <li>Simulated email & SMS notification inbox</li>
        <li>Booking confirmation and payment alert audit stream</li>
        <li>Structured logging with request ID, method, path, duration</li>
        <li>Rate limiting via SlowAPI per-IP</li>
      </ul>
    </td>
  </tr>
</table>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🚀 Quick Start

### Pre-loaded Demo Accounts

Run the seeder to populate Apollo, Metropolis, Dr. Lal PathLabs centres and tests:

```bash
python -m app.seed
# Or click "Seed Demo Data" directly in the web dashboard!
```

| Role | Email | Password |
|---|---|---|
| Demo Patient | `patient@evehealthcare.com` | `PatientPass123!` |
| Demo Admin | `admin@evehealthcare.com` | `AdminPass123!` |

---

### Option 1: Zero-Setup Local Run (Instant)

Works out of the box with zero external dependencies (async SQLite + automatic Postgres fallback):

```bash
# 1. Create and activate virtual environment
py -3.12 -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
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

### Option 3: Local Setup (Manual)

```bash
git clone https://github.com/your-username/eve-healthcare.git
cd eve-healthcare

python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eve_healthcare
# REDIS_URL=redis://localhost:6379/0

createdb eve_healthcare
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 📡 API Endpoints

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
| GET | `/api/v1/diagnostics/centres/{id}/tests` | List centre tests | No |

### Bookings

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/bookings/` | Create a booking | Yes |
| GET | `/api/v1/bookings/` | List user bookings (paginated) | Yes |
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

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🔧 Example Requests

<details>
<summary><b>1. Sign Up</b></summary>

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
</details>

<details>
<summary><b>2. Login</b></summary>

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "SecurePass123!"
  }'
```
</details>

<details>
<summary><b>3. Create a Diagnostic Centre (Admin)</b></summary>

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
</details>

<details>
<summary><b>4. Create a Booking</b></summary>

```bash
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{
    "centre_test_id": "<CENTRE_TEST_UUID>",
    "appointment_datetime": "2026-10-01T10:00:00Z"
  }'
```
</details>

<details>
<summary><b>5. Process Payment</b></summary>

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -d '{"booking_id": "<BOOKING_UUID>"}'
```
</details>

<details>
<summary><b>6. Idempotent Webhook (Payment Status Update)</b></summary>

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
</details>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🗄️ Database Schema

```
+------------------+     +------------------------+     +------------------+
|     users        |     |  diagnostic_centres    |     | diagnostic_tests |
+------------------+     +------------------------+     +------------------+
| id (PK, UUID)    |     | id (PK, UUID)          |     | id (PK, UUID)    |
| email (unique)   |     | name                   |     | name             |
| full_name        |     | address                |     | description      |
| phone            |     | city                   |     | category         |
| hashed_password  |     | state                  |     | created_at       |
| is_active        |     | pincode                |     +--------+---------+
| is_admin         |     | phone                  |              |
| created_at       |     | is_active              |              |
+-------+----------+     | created_at             |              |
        |                +------------+-----------+              |
        |                             |                          |
        |                +------------+---------------------------+
        |                |          centre_tests                  |
        |                +----------------------------------------+
        |                | id (PK, UUID)                          |
        |                | centre_id (FK -> diagnostic_centres)   |
        |                | test_id   (FK -> diagnostic_tests)     |
        |                | price (Numeric)                        |
        |                | is_available                           |
        |                | UNIQUE(centre_id, test_id)             |
        |                +---------------+------------------------+
        |                                |
+-------+--------------------------------+--------+
|                  bookings                      |
+------------------------------------------------+
| id (PK, UUID)                                  |
| booking_reference (unique, e.g. EVE-XXXXXXXX)  |
| user_id (FK -> users)                          |
| centre_test_id (FK -> centre_tests)            |
| appointment_datetime                           |
| amount (Numeric)                               |
| status (PENDING|CONFIRMED|FAILED|CANCELLED)    |
| created_at / updated_at                        |
+----------------------+-------------------------+
                       |
+----------------------+-------------------------+
|                  payments                      |
+------------------------------------------------+
| id (PK, UUID)                                  |
| booking_id (FK -> bookings)                    |
| transaction_id (unique, e.g. TXN-XXXX)         |
| amount (Numeric)                               |
| status (PENDING|SUCCESS|FAILED)                |
| payment_method                                 |
| created_at / updated_at                        |
+------------------------------------------------+

+------------------------------------------------+
|              webhook_events                    |
+------------------------------------------------+
| id (PK, UUID)                                  |
| event_id (unique - external idempotency key)   |
| event_type                                     |
| payload (JSON)                                 |
| processed (Boolean)                            |
| processed_at / created_at                      |
+------------------------------------------------+
```

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🏛️ Architecture & Design Decisions

```
+---------------------------+
|   Routers (API Layer)     |  HTTP request/response, validation, auth
+---------------------------+
              |
+---------------------------+
|  Services (Business Logic)|  DB queries, orchestration, state machine
+---------------------------+
              |
+---------------------------+
|   Models (Data Layer)     |  SQLAlchemy ORM, UUID PKs, async sessions
+---------------------------+
       |              |
+------------+  +-----------+
|  Schemas   |  | Exceptions|
| (Pydantic) |  |  (Custom) |
+------------+  +-----------+
```

| Design Decision | Rationale |
|---|---|
| UUID Primary Keys | Prevent enumeration attacks, enable distributed ID generation |
| Async Everything | FastAPI + asyncpg + SQLAlchemy async for maximum throughput |
| Junction Table (centre_tests) | Same test at different prices across different centres |
| Webhook Idempotency Table | Separate event_id tracking prevents duplicate processing |
| Booking Reference (EVE-XXXX) | Human-readable reference separate from internal UUID |
| Simulated Payments (80/20) | Realistic success/fail ratio for integration testing |
| HMAC Webhook Auth | Header-based cryptographic verification for webhook security |
| Soft Booking State Machine | PENDING to CONFIRMED/FAILED/CANCELLED prevents invalid transitions |

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## ✅ Bonus Features Implemented

- [x] **Redis Caching** - Diagnostic centres list/detail cached with TTL
- [x] **Celery Background Jobs** - Expired booking cleanup, async webhook processing with retries
- [x] **Docker & Docker Compose** - Full containerized setup (API, DB, Redis, Celery worker, Celery beat)
- [x] **Swagger/OpenAPI Docs** - Auto-generated at `/docs` and `/redoc`
- [x] **Unit & Integration Tests** - Comprehensive suite with pytest + httpx
- [x] **Structured Logging** - structlog with request ID, method, path, duration
- [x] **Pagination** - Generic paginated response for all list endpoints
- [x] **Rate Limiting** - SlowAPI per-IP rate limiting
- [x] **Retry Handling** - Celery tasks with exponential backoff for webhook processing
- [x] **Request Validation** - Pydantic v2 with custom validators (password strength, phone, future dates)

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🧪 Running Tests

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

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 📁 Project Structure

```
eve-healthcare/
+-- app/
|   +-- main.py                  # FastAPI application entry point
|   +-- config.py                # Environment-based configuration
|   +-- database.py              # Async SQLAlchemy engine & session
|   +-- security.py              # JWT & password hashing utilities
|   +-- dependencies.py          # FastAPI dependencies (auth, DB)
|   +-- models/
|   |   +-- user.py
|   |   +-- diagnostic.py
|   |   +-- booking.py
|   |   +-- payment.py
|   +-- schemas/
|   |   +-- user.py
|   |   +-- diagnostic.py
|   |   +-- booking.py
|   |   +-- payment.py
|   +-- routers/
|   |   +-- auth.py
|   |   +-- diagnostics.py
|   |   +-- bookings.py
|   |   +-- payments.py
|   +-- services/
|   |   +-- auth_service.py
|   |   +-- booking_service.py
|   |   +-- payment_service.py
|   |   +-- cache_service.py
|   +-- middleware/
|   |   +-- logging_middleware.py
|   +-- tasks/
|   |   +-- celery_app.py
|   +-- utils/
|       +-- exceptions.py
|       +-- pagination.py
+-- alembic/
+-- tests/
|   +-- conftest.py
|   +-- test_auth.py
|   +-- test_diagnostics.py
|   +-- test_bookings.py
|   +-- test_payments.py
+-- .env.example
+-- docker-compose.yml
+-- Dockerfile
+-- requirements.txt
+-- README.md
```

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 🔮 What I Would Improve With More Time

| # | Improvement | Reason |
|---|---|---|
| 1 | Refresh Token Rotation | Store in Redis with revocation support |
| 2 | Role-Based Access Control | Fine-grained permissions beyond admin/user |
| 3 | Email Notifications | Booking confirmation/cancellation via Celery |
| 4 | API Versioning | More robust versioning strategy |
| 5 | PgBouncer | Database connection pooling for production |
| 6 | GitHub Actions CI/CD | Automated testing and deployment |
| 7 | Prometheus + Grafana | Production monitoring dashboards |
| 8 | Audit Logging | Track all state changes for compliance |
| 9 | Full-Text Search | Search across centres and tests |
| 10 | WebSocket | Real-time booking status updates |

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

## 📝 Assumptions

1. A single user creates bookings for themselves (no "book for someone else" flow)
2. Each booking is for exactly one test at one centre
3. Appointment datetime is validated to be in the future
4. Only PENDING bookings can be cancelled
5. Payment amount is derived from centre_test price at booking time (price lock)
6. Webhook events are authenticated via shared secret header (X-Webhook-Secret)
7. The first admin user should be created manually or via a management script

<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0e1a,20:0d2137,40:0a3d62,60:1a5276,80:0d2137,100:0a0e1a&height=120&section=footer" />

**Eve DiagnoSync - Built as a production-grade backend engineering assignment**

*Async from the ground up. Idempotent by design. Secure by default.*

</div>