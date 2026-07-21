from typing import TYPE_CHECKING

from ..database import Base
from .employee_skill import employee_skills
from sqlalchemy import Integer, String, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .address import Address
    from .skills import Skill


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(10))
    department: Mapped[str] = mapped_column(String(100))
    designation: Mapped[str] = mapped_column(String(100))
    salary: Mapped[int] = mapped_column(Integer)
    experience: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary=employee_skills,
        back_populates="employees",
    )
    address: Mapped["Address | None"] = relationship(
        "Address",
        back_populates="employee",
        uselist=False,
        cascade="all, delete-orphan",
    )
