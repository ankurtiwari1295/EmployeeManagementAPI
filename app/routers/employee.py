from typing import Literal

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeListResponse,
)
from ..services.employee_service import (
    create_new_employee,
    delete_employee,
    filter_employees,
    get_employee_by_id,
    partially_update_employee,
    update_employee,
)

from ..dependencies.auth import get_current_user
from ..models.user import User

from ..dependencies.permission import manager_or_admin

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.get(
    "/",
    response_model=EmployeeListResponse,
)
async def get_employees(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    department: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: Literal[
        "id",
        "first_name",
        "salary",
        "experience",
    ] = "id",
    sort_order: Literal["asc", "desc"] = "asc",
):
    return await filter_employees(
        db=db,
        department=department,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{id}",
    response_model=EmployeeResponse,
)
async def get_employee(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_employee_by_id(
        id=id,
        db=db,
    )


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    emp: EmployeeCreate,
    current_user: User = Depends(manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    return await create_new_employee(
        db=db,
        emp=emp,
    )


@router.put(
    "/{id}",
    response_model=EmployeeResponse,
)
async def replace_employee(
    id: int,
    emp: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    return await update_employee(
        id=id,
        emp=emp,
        db=db,
    )


@router.patch(
    "/{id}",
    response_model=EmployeeResponse,
)
async def patch_employee(
    id: int,
    emp: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await partially_update_employee(
        id=id,
        emp=emp,
        db=db,
    )


@router.delete("/{id}")
async def delete_employee_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    return await delete_employee(
        id=id,
        db=db,
    )
