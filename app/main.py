from fastapi import FastAPI

from app.routers import accounts

app = FastAPI()
app.include_router(accounts.router)
