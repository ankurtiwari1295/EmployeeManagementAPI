from fastapi import Depends

from .roles import require_roles
from ..models.user import User


async def admin_user(
    current_user: User = Depends(require_roles("admin")),
):
    return current_user


async def manager_or_admin(
    current_user: User = Depends(
        require_roles(
            "admin",
            "manager",
        )
    ),
):
    return current_user


async def authenticated_user(
    current_user: User = Depends(
        require_roles(
            "admin",
            "manager",
            "employee",
        )
    ),
):
    return current_user
