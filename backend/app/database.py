"""
Database Engine & Session Management Module
Location: backend/app/database.py

Configures the SQLAlchemy ORM connection engine, session factory,
and dependency injector for the FastAPI application and Alembic migrations.
Compliant with Twelve-Factor App methodology for cloud production deployment.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file (if present locally)
load_dotenv()

# -------------------------------------------------------------
# 1. Resolve Cloud Database Connection String (12-Factor Pattern)
# -------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Cloud providers (e.g. Railway, Render, Supabase) often supply 'mysql://...'
    # SQLAlchemy requires an explicit Python DBAPI driver prefix 'mysql+pymysql://'
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    # Localhost development fallback using individual credentials
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "food_ecommerce_db")

    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# -------------------------------------------------------------
# 2. Production-Grade Engine Configuration & Connection Pooling
# -------------------------------------------------------------
# pool_pre_ping=True tests connections prior to checkout to prevent stale disconnect errors.
# pool_recycle=300 refreshes connections every 5 minutes before MySQL idle timeouts kill them.
# pool_size=10 maintains a warm pool of active connections for high-throughput traffic.
# max_overflow=20 allows temporary burst capacity during traffic spikes.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# -------------------------------------------------------------
# 3. Session Factory & Declarative Base
# -------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -------------------------------------------------------------
# 4. Request-Scoped Session Dependency Injector
# -------------------------------------------------------------
def get_db():
    """
    FastAPI dependency that yields an isolated database session per HTTP request
    and guarantees safe connection closure upon response completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()