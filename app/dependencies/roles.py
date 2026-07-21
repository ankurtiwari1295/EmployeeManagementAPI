from fastapi import Depends, HTTPException, status

from .auth import get_current_user
from ..models.user import User


def require_roles(*allowed_roles: str):
    """
    Factory function.

    Returns a dependency that allows only users
    having one of the allowed roles.
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ):
        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker
