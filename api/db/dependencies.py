from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from api.env import settings

DATABASE_URL = settings.DATABASE_URL
# Create the database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create the session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
