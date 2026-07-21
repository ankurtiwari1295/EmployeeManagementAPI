from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class Address(BaseModel):
    city: str
    state: str
    country: str


class AddressUpdate(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str = Field(min_length=10, max_length=10)
    department: str
    designation: str
    salary: int = Field(gt=0)
    experience: float = Field(ge=0)
    is_active: bool
    skills: list[str] = Field(min_length=1)
    address: Address

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")

        return value

    @model_validator(mode="after")
    def validate_designation(self):
        if (
            self.experience < 3
            and self.designation.lower() == "senior software engineer"
        ):
            raise ValueError(
                "Senior Software Engineer requires at least 3 years of experience"
            )
        return self


class SkillResponse(BaseModel):
    id: int
    name: str


class AddressResponse(BaseModel):
    id: int
    city: str
    state: str
    country: str


class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    designation: str
    experience: float
    is_active: bool

    skills: list[SkillResponse] = []
    address: AddressResponse | None = None


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    skip: int
    limit: int


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    salary: int | None = None
    experience: float | None = None
    is_active: bool | None = None

    # PATCH can replace the complete skill collection.
    skills: list[str] | None = None

    # PATCH can update only selected address fields.
    address: AddressUpdate | None = None
