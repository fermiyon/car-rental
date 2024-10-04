from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserDisplay


def validate_year(value: int) -> int:
    current_year = datetime.now().year + 1
    if value > current_year:
        raise ValueError(
            f"Year cannot be in the future. Current year is {current_year}."
        )
    if value < 1900:
        raise ValueError("Year cannot be earlier than 1900")
    return value


class CarBase(BaseModel):
    owner_id: int
    make: str
    model: str
    year: int = Field(default=datetime.utcnow().year)
    transmission_type: str
    motor_type: str
    price_per_day: float
    description: Optional[str] = None
    is_listed: bool = True

    @field_validator("year")
    def validate_year_field(cls, value):
        return validate_year(value)

    class Config:
        from_attributes = True


class CarCreate(BaseModel):
    make: str
    model: str
    year: int = Field(default=datetime.utcnow().year)
    transmission_type: str
    motor_type: str
    price_per_day: float
    description: Optional[str] = None
    is_listed: bool = True

    @field_validator("year")
    def validate_year_field(cls, value):
        return validate_year(value)

    class Config:
        from_attributes = True


class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    transmission_type: Optional[str] = None
    motor_type: Optional[str] = None
    price_per_day: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_listed: Optional[bool] = None

    @field_validator("year")
    def validate_year_field(cls, value):
        if value is not None:  # Optional validation
            return validate_year(value)
        return value

    class Config:
        from_attributes = True


class CarDisplay(BaseModel):
    id: int
    owner: UserDisplay
    make: str
    model: str
    year: int
    transmission_type: str
    motor_type: str
    price_per_day: float
    description: Optional[str]
    is_listed: bool

    class Config:
        from_attributes = True
