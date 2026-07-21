from fastapi import HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token,
    verify_token_type,
)
from ..models.user import User

from .email_service import send_welcome_email


async def register_user(
    db: AsyncSession,
    user_data,
    background_tasks: BackgroundTasks,
):
    query = select(User).where(User.email == user_data.email)

    result = await db.execute(query)

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        role="employee",
        is_active=True,
    )

    db.add(new_user)

    try:
        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    # Only send the email after the user
    # has been successfully saved.
    background_tasks.add_task(
        send_welcome_email,
        new_user.email,
    )

    return new_user


async def login_user(
    db: AsyncSession,
    form_data: OAuth2PasswordRequestForm,
):
    # Find the user by email.
    query = select(User).where(User.email == form_data.username)

    result = await db.execute(query)

    user = result.scalar_one_or_none()

    # Use the same error for:
    # 1. email does not exist
    # 2. password is incorrect
    #
    # This avoids revealing which email addresses are registered.
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Compare the plain password from the request
    # against the stored Argon2 password hash.
    is_password_valid = verify_password(
        plain_password=form_data.password,
        hashed_password=user.hashed_password,
    )

    if not is_password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Disabled users should not receive new access tokens.
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

        # The standard JWT "sub" claim will contain the user ID.
        # JWT subjects should be strings.
        # JWT "sub" contains the user's ID.

    subject = str(user.id)

    access_token = create_access_token(
        subject=subject,
    )

    refresh_token = create_refresh_token(
        subject=subject,
    )

    # Store latest refresh token.
    user.refresh_token = refresh_token

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
):
    """
    Generate a new access token using a valid refresh token.
    """

    # Verify JWT signature and expiration.
    payload = decode_token(refresh_token)

    # Ensure the provided JWT is actually a refresh token.
    verify_token_type(
        payload,
        "refresh",
    )

    # Extract the user ID from the JWT.
    user_id = int(payload["sub"])

    # Verify that the user still exists.
    query = select(User).where(
        User.id == user_id,
    )

    result = await db.execute(query)

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    # Prevent disabled users from generating new access tokens.
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    # Ensure the refresh token matches the latest one
    # stored in the database.
    if user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    # Generate a fresh access token.
    access_token = create_access_token(
        subject=str(user.id),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


async def logout_user(
    db: AsyncSession,
    current_user: User,
):
    """
    Invalidate the current refresh token.
    """

    current_user.refresh_token = None

    await db.commit()

    return {
        "message": "Logged out successfully",
    }
