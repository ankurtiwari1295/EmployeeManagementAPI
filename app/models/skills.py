from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .employee_skill import employee_skills

if TYPE_CHECKING:
    from .employee import Employee


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        secondary=employee_skills,
        back_populates="skills",
    )
