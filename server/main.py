
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from auth import router as auth_router

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL .env faylida topilmadi")

engine = create_engine(DATABASE_URL)

app = FastAPI(
    title="AI Agronom API",
    description="Sun'iy intellekt asosidagi agronom platformasi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "AI Agronom server ishlayapti!"
    }


@app.get("/database")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar()
        }
