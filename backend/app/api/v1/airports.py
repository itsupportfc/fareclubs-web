from typing import List

from app.db.database import get_db
from app.db.models.air_data import Airport
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/airports", tags=["Airports"])


class AirportResponse(BaseModel):
    airport_code: str
    airport_name: str
    city_name: str
    city_code: str
    country_name: str
    country_code: str

    class Config:
        from_attributes = True


@router.get("/search", response_model=List[AirportResponse])
async def search_airports(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search airports by code, city name, or airport name.
    Returns matching airports for autocomplete.
    """
    search_pattern = f"%{q}%"

    # Search in airport_code, city_name, city_code, and airport_name
    query = (
        select(Airport)
        .where(
            or_(
                Airport.airport_code.ilike(search_pattern),
                Airport.city_code.ilike(search_pattern),
                Airport.city_name.ilike(search_pattern),
                Airport.airport_name.ilike(search_pattern),
            )
        )
        .limit(limit)
    )

    result = await db.execute(query)
    airports = result.scalars().all()

    return airports


@router.get("/{airport_code}", response_model=AirportResponse)
async def get_airport(
    airport_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get airport details by airport code.
    """
    query = select(Airport).where(Airport.airport_code == airport_code.upper())
    result = await db.execute(query)
    airport = result.scalar_one_or_none()

    if not airport:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Airport not found")

    return airport
