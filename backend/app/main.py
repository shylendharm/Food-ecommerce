"""
Main Application Entrypoint
Location: backend/app/main.py

Initializes the FastAPI application, configures CORS middleware,
and mounts all modular API routers.
Database schema is managed strictly via Alembic migrations.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all modular routers (including tracking & websockets)
from app.routes import menu, orders, auth, admin, payments, tracking

# Initialize the master FastAPI application
app = FastAPI(
    title="Food Ordering & Restaurant API",
    description="Full-stack food delivery backend built with FastAPI, SQLAlchemy, Redis, and WebSockets.",
    version="1.0.0"
)

# -------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) Middleware
# -------------------------------------------------------------
# Defense against SEC-03: Insecure CORS Wildcard with Credentials Enabled.
# The W3C CORS standard forbids combining allow_origins=["*"] with allow_credentials=True.
# We establish an explicit origin whitelist with environment variable extensibility.
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Permit dynamic addition of production URLs via environment variables
production_origin = os.getenv("PRODUCTION_FRONTEND_URL")
if production_origin:
    origins.append(production_origin)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins.extend([origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],       # Allow all standard headers (Content-Type, Authorization, etc.)
)

# -------------------------------------------------------------
# Mount the Modular Routers
# -------------------------------------------------------------
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(tracking.router)


# -------------------------------------------------------------
# Health Check / Root Endpoint
# -------------------------------------------------------------
@app.get("/", tags=["Health Check"])
def root():
    """
    Root endpoint to quickly verify that the server is online and running.
    """
    return {
        "status": "online",
        "message": "Welcome to the Food Ordering API!",
        "documentation": "/docs"
    }