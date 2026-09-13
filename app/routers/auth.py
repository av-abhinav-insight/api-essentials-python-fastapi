from fastapi import APIRouter

from app.auth import authenticate_user, create_access_token
from app.models.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    # Password is accepted but intentionally not checked - this endpoint only
    # demonstrates issuing a signed token for a known user, not real auth.
    user = authenticate_user(credentials.username)
    token = create_access_token(user)
    return LoginResponse(access_token=token)
