import os

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "local")

settings = Settings()
