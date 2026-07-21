from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    decode_token,
    oauth2_scheme,
    verify_token_type,
)
from ..database import get_db
from ..models.user import User


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate the JWT access token and return
    the currently authenticated user.
    """

    # Verify JWT signature and expiration.
    payload = decode_token(token)

    # Ensure the JWT is an access token.
    verify_token_type(
        payload=payload,
        expected_type="access",
    )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Fetch the user from the database.
    query = select(User).where(
        User.id == int(user_id),
    )

    result = await db.execute(query)

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Prevent disabled users from accessing APIs.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user
