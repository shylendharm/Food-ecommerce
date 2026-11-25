# FoodExpress - Real-Time Food Delivery & Restaurant Logistics Platform

A full-stack food ordering and restaurant logistics platform I built from scratch using FastAPI, SQLAlchemy, MySQL, Redis, and WebSockets.

The project is deployed and live in production:
- Live Application: https://foodexpress-app-hael.onrender.com
- API & Interactive Docs: https://food-ecommerce-q4mi.onrender.com/docs

---

## Why I Built This

I wanted to move beyond basic CRUD applications and build a system that reflects how production food delivery and restaurant logistics actually work behind the scenes. 

Instead of just storing items in a database and rendering lists, I focused on engineering the real-world operational challenges:
1. Preventing client-side price tampering: Recalculating totals on the server from authoritative database records rather than trusting client-submitted prices.
2. High-speed catalog delivery: Implementing the Cache-Aside pattern in Redis with wildcard cache invalidation when menu availability changes.
3. Live order dispatch: Streaming courier telemetry and order state transitions over an authenticated full-duplex WebSocket channel.
4. Defensive security: Protecting against Insecure Direct Object References (IDOR), SQL injection, DOM XSS, and authentication brute-forcing.

---

## What I Built (Core Features)

### 1. Customer Storefront & Cart
- Responsive UI with fast search and instant vegetarian/non-vegetarian category filtering.
- Client-side shopping cart with self-healing local storage and dynamic quantity management.
- Complete mobile optimization across phones, tablets, and desktop screens.

### 2. Authentication & Authorization
- Dual-path authentication: Google OAuth 2.0 Single Sign-On (Google Identity Services) and traditional email/password login.
- Passwords hashed using salted Bcrypt algorithms.
- Stateless authentication using cryptographically signed JSON Web Tokens (JWT) with role-based access control (Customer vs Admin).

### 3. Real-Time Order Tracking & Telemetry
- Interactive Leaflet.js map with route polyline and dynamic markers for restaurant, courier, and delivery address.
- Full-duplex WebSocket client that connects with a token handshake and streams live order state updates.
- Dynamic ETA computation and haversine distance calculation between the kitchen and customer coordinates.
- Finite state machine managing order lifecycles (PENDING, PREPARING, OUT_FOR_DELIVERY, DELIVERED) with customer cancellation guards.

### 4. Kitchen Display System (KDS) & Inventory Management
- Dedicated admin portal for restaurant kitchen staff to inspect incoming tickets in real time.
- Status advancing controls (advance ticket from Pending to Cooking, Cooking to Dispatched).
- Instant inventory toggle to mark dishes in stock or out of stock with automatic Redis cache invalidation.

### 5. Simulated Payment Gateway
- Supports Cash on Delivery (COD) and Online Sandbox payment methods.
- Payment gateway intent creation and webhook verification with HMAC-SHA256 signatures before updating payment ledger states.

---

## System Architecture

```text
+-------------------------------------------------------------+
|                      Client Layer                           |
|       Vanilla ES6+ JavaScript, HTML5, CSS3 Variables        |
|           Hosted on Render Global CDN (Static Site)         |
+-------------------------------------------------------------+
                              |
                     HTTPS / WSS Requests
                              |
                              v
+-------------------------------------------------------------+
|                      Backend API                            |
|             Python 3.12 / FastAPI / Uvicorn                 |
|       CORS Middleware Whitelist + Rate Limiting Guard       |
+-------------------------------------------------------------+
           |                                  |
    Cache-Aside (TTL)               Relational Transactions
           |                                  |
           v                                  v
+-----------------------+          +--------------------------+
|      Redis Cache      |          |       MySQL 8.0          |
|    (Upstash Cloud)    |          |   (TiDB Serverless)      |
| Menu RAM & Rate Limit |          | Orders, Users, Inventory |
+-----------------------+          +--------------------------+
```

---

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM), Uvicorn, PyMySQL, Pydantic V2, Alembic
- Frontend: Vanilla JavaScript (ES6+), HTML5, CSS3 with custom design tokens, Leaflet.js
- Database: MySQL 8.0 wire-compatible (TiDB Cloud Serverless on AWS Singapore)
- Cache: Redis 7.x (Upstash Serverless with native TLS on AWS Singapore)
- Authentication: Google Identity Services OAuth 2.0, PyJWT, Passlib (Bcrypt)
- Hosting & CI/CD: Render (Python Web Service + Static Site CDN connected to GitHub)
- Testing: Pytest (60 automated unit, integration, and security regression tests)

---

## Security Hardening (OWASP Top 10 Focus)

During development, I performed a security audit across the codebase and implemented defensive measures:
- IDOR Defense: Every order retrieval and payment lookup validates that the requesting user's JWT sub claim matches the record's user_id, with an administrative override for restaurant managers.
- Price Authority: Order total amounts and line-item snapshots are frozen from the server database at checkout time. Any price sent by the client is discarded.
- Brute-Force Throttling: Integrated an atomic Redis counter on login and register routes that temporarily blocks IP addresses exceeding failed attempt thresholds.
- Cryptographic Boot Guards: The backend prevents startup in production mode if a default or fallback JWT secret key is detected.
- XSS Sanitization: Dynamic order addresses and customer notes rendered in Leaflet map popups and modal dialogues pass through strict HTML entity escaping.
- WebSocket Handshake Validation: The WebSocket endpoint extracts the JWT from the handshake query parameters, validates the token signature, and checks user authorization before accepting the socket connection (rejecting unauthorized connections with policy violation code 1008).

---

## Automated Test Suite

I wrote an automated test suite covering all critical business paths. All 60 automated tests run and pass cleanly:

```bash
pytest backend/tests
```

Test coverage includes:
- Administrative menu creation, ticket status updates, and stock toggles
- Customer registration, login, and Google OAuth payload handling
- Redis cache-aside reads, writes, and wildcard cache purging
- Logistics distance and ETA calculations
- Order placement, IDOR access controls, and customer cancellation state machines
- Payment intent creation, ledger verification, and HMAC webhook signature validation

---

## Local Development Setup

To run this project locally:

### 1. Clone the repository
```bash
git clone https://github.com/shylendharm/Food-ecommerce.git
cd Food-ecommerce
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
# Copy .env.example to .env and fill in your local MySQL and Redis credentials

# Run database migrations and seed menu data
cd backend
python seed.py

# Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
Serve the frontend directory using any local HTTP server:

```bash
cd frontend
python -m http.server 5500
```

Open your browser and navigate to: `http://localhost:5500/index.html`

---

## Author

- Name: Shylendhar M
- Email: shylendharm369@gmail.com
- GitHub: https://github.com/shylendharm