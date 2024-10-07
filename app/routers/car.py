"""
Car Router

This module provides endpoints for managing car entries in the database.
It allows users to create, read, update, and delete car records.
Some actions require user authentication.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth import oauth2
from app.core.database import get_db
from app.schemas.car import CarCreate, CarDisplay, CarUpdate
from app.schemas.rental import RentalPeriod
from app.schemas.enums import (
    CarEngineType,
    CarSearchSortDirection,
    CarSearchSortType,
    CarTransmissionType,
    UserType,
)
from app.services import car
from app.utils import constants

router = APIRouter(prefix="/cars", tags=["cars"])


@router.post(
    "/",
    response_model=CarDisplay,
    summary="Create a car",
    description="Create a new car entry. Requires authenticated user.",
)
def create_car(
    request: CarCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.complete_user_profile_only),
):
    """
    Create a new car entry in the database.

    Args:
        request (CarCreate): The details of the car to create.
        db (Session): Database session dependency.
        current_user (Any): The authenticated user creating the car.

    Returns:
        CarDisplay: The newly created car.
    """
    return car.create_car(db, request, current_user.id)


@router.get(
    "/",
    response_model=List[CarDisplay],
    summary="List all cars",
    description="Retrieve a paginated list of all cars from the database.",
)
def list_cars(
    db: Session = Depends(get_db),
    skip: int = Query(
        0, ge=0, description="Number of records to skip (used for pagination)"
    ),
    limit: int = Query(
        constants.QUERY_LIMIT_DEFAULT,
        ge=1,
        le=constants.QUERY_LIMIT_MAX,
        description="Maximum number of records to return",
    ),
) -> List[CarDisplay]:
    """
    Retrieve all car entries from the database with pagination options.

    Args:
        db (Session): Database session dependency.
        skip (int): Number of records to skip (used for pagination).
        limit (int): Maximum number of records to return (used for pagination).

    Returns:
        List[CarBase]: A list of cars in the database based on pagination.
    """
    return car.get_cars(db, skip=skip, limit=limit)


@router.get(
    path="/search",
    summary="Search cars",
    description="Filter car search based on distance, city, booking periods, engine type"
    " transmission type, price and make. Sort result accordingly.",
)
def search_car(
    distance_km: float = Query(
        default=None,
        ge=1,
        description="Radius of the search in kilometers "
        "(ignored if search_in_city is also set)",
    ),
    search_in_city: str = Query(default=None, description="Name of the city to search"),
    renter_lat: float = Query(
        None, ge=-90, le=90, description="Latitude of the user's location"
    ),
    renter_lon: float = Query(
        None, ge=-180, le=180, description="Longitude of the user's location"
    ),
    availability_period: RentalPeriod = Depends(),
    engine_type: CarEngineType = Query(None, description="Select an engine type"),
    transmission_type: CarTransmissionType = Query(
        None, description="Select a transmission type"
    ),
    price_min: int = Query(None, ge=0, description="Minimum daily price for the rent"),
    price_max: int = Query(None, ge=1, description="Maximum daily price for the rent"),
    make: str = Query(None, description="Make of the car"),
    sort: CarSearchSortType = Query(None, description="Sort parameter"),
    sort_direction: CarSearchSortDirection = Query(None, description="Sort direction"),
    skip: int = Query(
        default=0, ge=0, description="Used for pagination for the requests."
    ),
    limit: int = Query(
        constants.QUERY_LIMIT_DEFAULT,
        ge=1,
        le=constants.QUERY_LIMIT_MAX,
        description="Length of the response list",
    ),
    db: Session = Depends(get_db),
):
    return car.search_cars(
        distance_km=distance_km,
        renter_lat=renter_lat,
        renter_lon=renter_lon,
        availability_period=availability_period,
        search_in_city=search_in_city,
        engine_type=engine_type,
        transmission_type=transmission_type,
        price_min=price_min,
        price_max=price_max,
        make=make,
        sort=sort,
        sort_direction=sort_direction,
        skip=skip,
        limit=min(limit, constants.QUERY_LIMIT_MAX),
        db=db,
    )


@router.get(
    "/{car_id}",
    response_model=CarDisplay,
    summary="Get car by ID",
    description="Retrieve details of a car by its ID.",
)
def get_car(
    car_id: int = Path(..., ge=1, description="The ID of the car to retrieve"),
    db: Session = Depends(get_db),
) -> CarDisplay:
    """
    Retrieve a car entry from the database by its ID.

    Args:
        car_id (int): The ID of the car to retrieve.
        db (Session): Database session dependency.

    Returns:
        CarDisplay: The details of the car with the specified ID.
    """
    try:
        db_car = car.get_car(db, car_id)
        # Check if the database car record has different model than response model
        CarDisplay.model_validate(db_car)
        return db_car
    except ValidationError as e:
        # Validation Error for pydantic
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error occurred: {e.errors()}",
        )

    except Exception as e:
        # Catch any other unforeseen errors.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.put(
    "/{car_id}",
    summary="Update car details",
    description="Update the details of a car by its ID. Requires authentication.",
)
def update_car(
    car_id: int,
    request: CarUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Update a car entry in the database by its ID.

    Args:
        car_id (int): The ID of the car to update.
        request (CarUpdate): The updated car data.
        db (Session): Database session dependency.
        current_user (Any): The authenticated user performing the update.

    Returns:
        Any: The updated car data after the operation.
    """
    db_car = car.get_car(db, car_id)

    if current_user.user_type != UserType.ADMIN and db_car.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this car",
        )

    return car.update_car(db, car_id, request)


@router.delete(
    "/{car_id}",
    summary="Delete a car",
    description="Delete a car from the database by its ID. Requires authentication.",
    tags=["cars", "admin"],
)
def delete_car(
    car_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user),
):
    """
    Delete a car entry from the database by its ID.

    Args:
        car_id (int): The ID of the car to delete.
        db (Session): Database session dependency.
        current_user (Any): The authenticated user performing the deletion.

    Returns:
        Any: The result of the delete operation.
    """
    db_car = car.get_car(db, car_id)

    if current_user.user_type != UserType.ADMIN and db_car.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this car",
        )

    return car.delete_car(db, car_id)
