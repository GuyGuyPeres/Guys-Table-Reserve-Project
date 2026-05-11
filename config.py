import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI = os.getenv("MONGO_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")
    SES_REGION = os.getenv("SES_REGION", "us-east-1")

settings = Settings()