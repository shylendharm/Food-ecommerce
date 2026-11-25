"""Database engine configuration and session dependency."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "food_ecommerce_db")

    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Connection pooling engine
# max_overflow=20 allows temporary burst capacity during traffic spikes.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Session factory and declarative base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database session dependency
def get_db():
    """Yield database session for request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()