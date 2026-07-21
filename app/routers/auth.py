from fastapi import APIRouter, Depends, status
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.user import (
    UserRegister,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
)
from ..services.auth_service import (
    register_user,
    login_user,
    refresh_access_token,
    logout_user,
)
from fastapi.security import OAuth2PasswordRequestForm
from ..dependencies.auth import get_current_user
from ..models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(
        db=db,
        user_data=user_data,
        background_tasks=background_tasks,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await login_user(
        db=db,
        form_data=form_data,
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    current_user: User = Depends(
        get_current_user,
    ),
    db: AsyncSession = Depends(get_db),
):
    return await logout_user(
        db=db,
        current_user=current_user,
    )
