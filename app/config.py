import os

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    AUTH_TOKEN_SECRET: str = os.getenv("AUTH_TOKEN_SECRET", "dev-only-insecure-secret")
    AUTH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "30"))
    FRAUD_SERVICE_URL: str = os.getenv("FRAUD_SERVICE_URL", "http://localhost:8001")

settings = Settings()
