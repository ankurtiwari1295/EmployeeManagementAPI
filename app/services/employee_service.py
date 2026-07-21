from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.address import Address
from ..models.employee import Employee
from ..models.skills import Skill


async def get_employee_by_id(
    id: int,
    db: AsyncSession,
):
    # Eagerly load relationships.
    # In async SQLAlchemy, allowing FastAPI/Pydantic to lazy-load a
    # relationship during response serialization can cause MissingGreenlet.
    query = (
        select(Employee)
        .options(
            selectinload(Employee.address),
            selectinload(Employee.skills),
        )
        .where(Employee.id == id)
    )

    result = await db.execute(query)

    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return employee


async def filter_employees(
    db: AsyncSession,
    department: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc",
):
    # Load relationships for all returned employees.
    # selectinload avoids one lazy-loading query per employee.
    query = select(Employee).options(
        selectinload(Employee.address),
        selectinload(Employee.skills),
    )

    # All where() conditions added below are combined with AND.
    if department is not None:
        query = query.where(Employee.department.ilike(department))

    if is_active is not None:
        query = query.where(Employee.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"

        # Search matches any one of these fields because we use OR.
        query = query.where(
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.email.ilike(search_pattern),
                Employee.designation.ilike(search_pattern),
            )
        )

    # Count after filtering but before pagination.
    # This gives the frontend the total number of matching records.
    count_query = select(func.count()).select_from(query.subquery())

    total = await db.scalar(count_query)

    # Whitelist sortable columns.
    # Never directly use a user-provided column name in a SQL query.
    sortable_fields = {
        "id": Employee.id,
        "first_name": Employee.first_name,
        "salary": Employee.salary,
        "experience": Employee.experience,
    }

    sort_column = sortable_fields.get(sort_by)

    if sort_column is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort field",
        )

    # Employee.id is used as a secondary sort for stable pagination
    # when multiple employees have the same primary sort value.
    if sort_order == "desc":
        query = query.order_by(
            sort_column.desc(),
            Employee.id.asc(),
        )
    else:
        query = query.order_by(
            sort_column.asc(),
            Employee.id.asc(),
        )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)

    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


async def resolve_skills(
    db: AsyncSession,
    skill_names: list[str],
) -> list[Skill]:
    """
    Convert skill names from the API request into Skill ORM objects.

    Existing skills are reused.
    New skills are created automatically.

    Example:
    ["React", " python ", "REACT"]
    becomes:
    [Skill(name="react"), Skill(name="python")]
    """

    # Normalize and remove duplicate names.
    normalized_names = {
        skill_name.strip().lower() for skill_name in skill_names if skill_name.strip()
    }

    employee_skills = []

    for skill_name in normalized_names:
        query = select(Skill).where(Skill.name == skill_name)

        result = await db.execute(query)

        existing_skill = result.scalar_one_or_none()

        if existing_skill is not None:
            employee_skills.append(existing_skill)
        else:
            employee_skills.append(Skill(name=skill_name))

    return employee_skills


async def create_new_employee(
    db: AsyncSession,
    emp,
):
    # Convert the Pydantic request into a dictionary containing
    # only columns that belong directly to the employees table.
    #
    # skills and address are relationships, so they are handled separately.
    employee_data = emp.model_dump(
        exclude={
            "skills",
            "address",
        }
    )

    # Create the Employee ORM object.
    new_employee = Employee(**employee_data)

    # Create and attach the one-to-one Address ORM object.
    #
    # We do not manually provide employee_id.
    # SQLAlchemy fills it automatically through the relationship.
    if emp.address is not None:
        new_employee.address = Address(**emp.address.model_dump())

    # Convert the list of skill names into Skill ORM objects.
    #
    # resolve_skills():
    # 1. normalizes names
    # 2. removes duplicate names
    # 3. reuses existing Skill rows
    # 4. creates new Skill objects when needed
    new_employee.skills = await resolve_skills(
        db=db,
        skill_names=emp.skills,
    )

    # Adding the Employee is enough because SQLAlchemy relationships
    # will also persist the related address, new skills,
    # and employee_skills association rows.
    db.add(new_employee)

    try:
        # One transaction saves:
        # 1. employee
        # 2. address
        # 3. any new skills
        # 4. employee_skills association rows
        await db.commit()

    except IntegrityError:
        # A failed commit leaves the session in a failed state.
        # Rollback is required before the session can be used again.
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Employee or skill already exists",
        )

    # Re-query the employee with address and skills eagerly loaded.
    #
    # Returning new_employee directly could cause MissingGreenlet
    # if FastAPI tries to access an unloaded relationship while
    # serializing the response.
    return await get_employee_by_id(
        id=new_employee.id,
        db=db,
    )


async def update_employee(
    id: int,
    emp,
    db: AsyncSession,
):
    existing_employee = await get_employee_by_id(
        id=id,
        db=db,
    )

    # Update direct columns belonging to the employees table.
    employee_data = emp.model_dump(
        exclude={
            "skills",
            "address",
        }
    )

    for key, value in employee_data.items():
        setattr(existing_employee, key, value)

    # PUT is a complete replacement.
    # Replace the existing address values with request values.
    if existing_employee.address is not None:
        address_data = emp.address.model_dump()

        for key, value in address_data.items():
            setattr(existing_employee.address, key, value)

    else:
        # Older employees may not have an address yet.
        existing_employee.address = Address(**emp.address.model_dump())

    # Replace the complete many-to-many skill collection.
    #
    # SQLAlchemy updates employee_skills automatically:
    # old associations are removed and new ones are inserted.
    existing_employee.skills = await resolve_skills(
        db=db,
        skill_names=emp.skills,
    )

    try:
        # All employee, address, and skill changes happen
        # inside one database transaction.
        await db.commit()

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Employee or skill already exists",
        )

    # Reload relationships before response serialization.
    return await get_employee_by_id(
        id=id,
        db=db,
    )


async def partially_update_employee(
    id: int,
    emp,
    db: AsyncSession,
):
    # Load the employee together with address and skills.
    existing_employee = await get_employee_by_id(
        id=id,
        db=db,
    )

    # model_fields_set contains only fields actually sent by the client.
    #
    # Example:
    # PATCH {"department": "Dev"}
    # provided_fields = {"department"}
    provided_fields = emp.model_fields_set

    if not provided_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    # Update only direct columns from the employees table.
    # Relationships are handled separately below.
    employee_data = emp.model_dump(
        exclude_unset=True,
        exclude={
            "skills",
            "address",
        },
    )

    for key, value in employee_data.items():
        setattr(existing_employee, key, value)

    # Handle address only if the client actually sent "address".
    if "address" in provided_fields:

        # address: null means remove the employee's address.
        if emp.address is None:
            existing_employee.address = None

        # Employee already has an address:
        # update only the address fields provided by the client.
        elif existing_employee.address is not None:
            address_data = emp.address.model_dump(exclude_unset=True)

            for key, value in address_data.items():
                setattr(
                    existing_employee.address,
                    key,
                    value,
                )

        # Employee has no existing address.
        else:
            address_data = emp.address.model_dump(exclude_unset=True)

            # A new address requires all database-required fields.
            required_fields = {
                "city",
                "state",
                "country",
            }

            missing_fields = required_fields - address_data.keys()

            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Complete address is required when "
                        "creating a new address. Missing fields: "
                        f"{', '.join(sorted(missing_fields))}"
                    ),
                )

            existing_employee.address = Address(**address_data)

    # Handle skills only if the client actually sent "skills".
    if "skills" in provided_fields:

        # skills: null or skills: [] removes all associations.
        if emp.skills is None:
            existing_employee.skills = []

        else:
            existing_employee.skills = await resolve_skills(
                db=db,
                skill_names=emp.skills,
            )

    try:
        # Employee columns, address changes, and skill associations
        # are committed together as one transaction.
        await db.commit()

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Employee or skill already exists",
        )

    # Reload all relationships before FastAPI serializes the response.
    return await get_employee_by_id(
        id=id,
        db=db,
    )


async def delete_employee(
    id: int,
    db: AsyncSession,
):
    employee = await get_employee_by_id(
        id=id,
        db=db,
    )

    await db.delete(employee)
    await db.commit()

    return {
        "message": "Employee deleted successfully",
    }
