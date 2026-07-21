from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Never store the user's plain-text password.
    # Registration will hash the password before saving it here.

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Later we will use this for role-based authorization (RBAC).
    # Example roles: admin, manager, employee.

    role: Mapped[str] = mapped_column(String(50), nullable=False, default="employee")

    # Allows us to disable an account without deleting it.

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    refresh_token: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
