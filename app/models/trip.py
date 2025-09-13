"""Trip models for travel planning and management."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date


class TripRequest(BaseModel):
    """Request model for creating a new trip."""
    destination: str = Field(..., min_length=1, max_length=100, description="Trip destination")
    departure_city: str = Field(..., min_length=1, max_length=100, description="City of departure", alias="departureCity")
    start_date: date = Field(..., description="Trip start date", alias="startDate")
    end_date: date = Field(..., description="Trip end date", alias="endDate")
    total_budget: str = Field(..., description="Total budget for the trip", alias="totalBudget")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., USD)")
    total_adult_travellers: str = Field(..., description="Number of adult travelers", alias="totalAdultTravellers")
    total_child_travellers: int = Field(..., ge=0, description="Number of child travelers", alias="totalChildTravellers")
    travelling_with_pets: bool = Field(default=False, description="Whether traveling with pets", alias="travellingWithPets")
    stay_preference: List[str] = Field(default=[], description="Accommodation preferences", alias="stayePrefrence")
    transportation_preference: List[str] = Field(default=[], description="Transportation preferences", alias="transporationPreference")
    extra_activities: List[str] = Field(default=[], description="Extra activities preferences", alias="extraActivites")
    special_requirements: str = Field(default="", description="Any special requirements", alias="specialRequrements")

    class Config:
        populate_by_name = True


class TripResponse(BaseModel):
    """Response model for trip data."""
    id: str = Field(..., description="Unique trip identifier")
    user_id: str = Field(..., description="User ID who owns this trip")
    destination: str
    departure_city: str
    start_date: date
    end_date: date
    total_budget: str
    currency: str
    total_adult_travellers: str
    total_child_travellers: int
    travelling_with_pets: bool
    stay_preference: List[str]
    transportation_preference: List[str]
    extra_activities: List[str]
    special_requirements: str
    created_at: datetime
    updated_at: datetime


class TripCreateResponse(BaseModel):
    """Response model for trip creation."""
    success: bool
    message: str
    trip: Optional[TripResponse] = None


class TripSummary(BaseModel):
    """Simplified trip summary for list responses."""
    id: str = Field(..., description="Unique trip identifier")
    created_at: datetime
    destination: str
    departure_city: str


class TripListResponse(BaseModel):
    """Response model for listing trips."""
    success: bool
    message: str
    trips: List[TripSummary] = []
    total_count: int = 0
