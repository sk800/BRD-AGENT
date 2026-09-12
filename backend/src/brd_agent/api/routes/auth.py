from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from brd_agent.api.dependencies.auth import get_auth_service
from brd_agent.api.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse
from brd_agent.core.exceptions import AuthError
from brd_agent.core.security import create_access_token
from brd_agent.domain.models.user import UserCreate
from brd_agent.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    try:
        user = await auth_service.signup(
            UserCreate(
                email=payload.email,
                full_name=payload.full_name,
                password=payload.password,
            )
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    access_token = create_access_token(user.id)
    return AuthResponse(
        user=UserResponse.model_validate(user.model_dump()),
        access_token=access_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    try:
        user, access_token = await auth_service.login(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return AuthResponse(
        user=UserResponse.model_validate(user.model_dump()),
        access_token=access_token,
    )
