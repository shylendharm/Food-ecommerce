import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Load the secret variables from your .env file
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "food_ecommerce_db")

# 2. Build the MySQL connection string using the PyMySQL driver
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

# 3. Create the SQLAlchemy Engine # The engine manages the pool of connections to MySQL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 4. Create a SessionLocal factory so that Every time an API request comes in, it will use this to open a temporary conversation with MySQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Base class for our database models
Base = declarative_base()

# 6. Dependency function to give each API request its own database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Automatically closes the connection when the request finishes!