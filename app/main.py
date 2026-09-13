import logging

from fastapi import FastAPI

from app.config import settings
from app.exceptions.handlers import register_exception_handlers
from app.routers import accounts, transfers

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI()
app.include_router(accounts.router)
app.include_router(transfers.router)
register_exception_handlers(app)
