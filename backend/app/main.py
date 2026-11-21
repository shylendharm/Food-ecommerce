"""
Main Application Entrypoint
Location: backend/app/main.py

Initializes the FastAPI application, configures CORS middleware,
creates database tables, and mounts all modular API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database and metadata to ensure all tables exist
from app.database import engine, Base

# Import all modular routers (including tracking & websockets!)
from app.routes import menu, orders, auth, admin, payments, tracking

# Safe auto-creation: Creates any missing tables in MySQL on startup
Base.metadata.create_all(bind=engine)

# Initialize the master FastAPI application
app = FastAPI(
    title="Food Ordering & Restaurant API",
    description="Full-stack food delivery backend built with FastAPI, SQLAlchemy, Redis, and WebSockets.",
    version="1.0.0"
)

# -------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) Middleware
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # For local development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],       # Allow all headers (Content-Type, Authorization, etc.)
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