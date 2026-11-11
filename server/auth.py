
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL .env faylida topilmadi")

engine = create_engine(DATABASE_URL)
password_hash = PasswordHash.recommended()


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str | None = None
    phone_number: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_contact(self):
        if not self.email and not self.phone_number:
            raise ValueError("Email yoki telefon raqami kerak")
        return self


class LoginRequest(BaseModel):
    email: str | None = None
    phone_number: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_contact(self):
        if not self.email and not self.phone_number:
            raise ValueError("Email yoki telefon raqami kerak")
        return self


@router.post("/register")
def register(data: RegisterRequest):
    email = data.email.strip().lower() if data.email else None
    phone = data.phone_number.strip() if data.phone_number else None

    hashed_password = password_hash.hash(data.password)

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO users
                    (full_name, email, phone_number,
                     auth_provider, password_hash)
                    VALUES
                    (:name, :email, :phone, :provider, :password)
                    RETURNING id, full_name, email, phone_number
                """),
                {
                    "name": data.full_name.strip(),
                    "email": email,
                    "phone": phone,
                    "provider": "email" if email else "phone",
                    "password": hashed_password
                }
            )

            user = result.mappings().one()

            return {
                "message": "Akkaunt muvaffaqiyatli yaratildi",
                "user": dict(user)
            }

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Bu email yoki telefon raqami allaqachon ro'yxatdan o'tgan"
        )


@router.post("/login")
def login(data: LoginRequest):
    email = data.email.strip().lower() if data.email else None
    phone = data.phone_number.strip() if data.phone_number else None

    with engine.connect() as connection:
        if email:
            result = connection.execute(
                text("""
                    SELECT id, full_name, email, phone_number, password_hash
                    FROM users
                    WHERE email = :email
                """),
                {"email": email}
            )
        else:
            result = connection.execute(
                text("""
                    SELECT id, full_name, email, phone_number, password_hash
                    FROM users
                    WHERE phone_number = :phone
                """),
                {"phone": phone}
            )

        user = result.mappings().first()

    if not user or not password_hash.verify(
        data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Telefon raqami yoki parol noto'g'ri"
        )

    return {
        "message": "Tizimga muvaffaqiyatli kirdingiz",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "phone_number": user["phone_number"]
        }
    }
