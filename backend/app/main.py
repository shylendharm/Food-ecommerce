"""FastAPI application entrypoint, middleware, and route mounting."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import menu, orders, auth, admin, payments, tracking

app = FastAPI(
    title="Food Ordering & Restaurant API",
    description="Full-stack food delivery backend built with FastAPI, SQLAlchemy, Redis, and WebSockets.",
    version="1.0.0"
)

# CORS origin configuration
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(tracking.router)


# Health check
@app.get("/", tags=["Health Check"])
def root():
    """Root health check endpoint."""
    return {
        "status": "online",
        "message": "Welcome to the Food Ordering API!",
        "documentation": "/docs"
    }