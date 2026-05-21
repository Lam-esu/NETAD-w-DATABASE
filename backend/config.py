import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-this")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///secure_cctv.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "")