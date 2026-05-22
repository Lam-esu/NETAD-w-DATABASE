import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "fallback-secret"
    )

    SQLALCHEMY_DATABASE_URI = (
        database_url
        or "sqlite:///securecctv.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CAMERA_SOURCE = os.environ.get(
        "CAMERA_SOURCE",
        0
    )