from sqlalchemy import Column, ForeignKey, Integer, Table

from ..database import Base

employee_skills = Table(
    "employee_skills",
    Base.metadata,
    Column(
        "employee_id",
        Integer,
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "skill_id",
        Integer,
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)
