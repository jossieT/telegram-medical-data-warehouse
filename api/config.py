import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database Config
    DB_NAME = os.getenv("DB_NAME", "medical_warehouse")
    DB_USER = os.getenv("DB_USER", "medical_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "medical_password")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5433")
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

settings = Settings()
