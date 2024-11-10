
from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import APIRouter
from dotenv import load_dotenv
import os


load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URI,
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"charset": "utf8mb4"},
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# INITIALIZE
router = APIRouter()

