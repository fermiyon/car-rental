from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, conint, constr

# Here under is what is added
from app.schemas.user import UserDisplay


# Review Schema
class ReviewBase(BaseModel):
    rental_id: int
    reviewer_id: int
    reviewee_id: int
    rating: conint(ge=1, le=5)  # Rating must be between 1 and 5
    comment: Optional[str] = None

    comment: constr(max_length=500)  # Comment must be max 500 characters


# class ReviewCreate(BaseModel):
#     rental_id: int
#     reviewer_id: int
#     reviewee_id: int
#     rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
#     comment: str = Field(..., max_length=500)

#     # ratting: conint(ge=1, le=5)
#     # comment: constr(max_length=500)


class ReviewCreate(BaseModel):
    rental_id: int
    reviewee_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: str = Field(..., max_length=500)

    # ratting: conint(ge=1, le=5)
    # comment: constr(max_length=500)


# class ReviewDisplay(ReviewCreate):
class ReviewDisplay(BaseModel):
    id: int
    # Here under is what is added
    rental_id: int
    # reviewer_id: int
    reviewer: UserDisplay
    reviewee: UserDisplay
    review_date: datetime

    class Config:
        orm_mode = True
