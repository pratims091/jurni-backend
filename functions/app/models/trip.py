"""Trip models for travel planning and management."""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, date


class DayActivitySchedule(BaseModel):
    """Daily activity schedule."""
    day: Optional[int] = Field(None, description="Day number")
    activityIds: Optional[List[int]] = Field(default_factory=list, description="List of activity IDs for this day")


class LayoverInfo(BaseModel):
    """Flight layover information."""
    city: Optional[str] = Field(None, description="Layover city")
    duration: Optional[str] = Field(None, description="Layover duration")


class FlightInfo(BaseModel):
    """Flight information."""
    id: Optional[str] = Field(None, description="Flight ID")
    airline: Optional[str] = Field(None, description="Airline name")
    flightNumber: Optional[str] = Field(None, description="Flight number")
    price: Optional[int] = Field(None, description="Flight price")
    duration: Optional[str] = Field(None, description="Flight duration")
    departure: Optional[str] = Field(None, description="Departure time")
    arrival: Optional[str] = Field(None, description="Arrival time")
    departureDate: Optional[str] = Field(None, description="Departure date")
    arrivalDate: Optional[str] = Field(None, description="Arrival date")
    stops: Optional[int] = Field(None, description="Number of stops")
    aircraft: Optional[str] = Field(None, description="Aircraft type")
    class_: Optional[str] = Field(None, alias="class", description="Flight class")
    amenities: Optional[List[str]] = Field(default_factory=list, description="Flight amenities")
    baggage: Optional[str] = Field(None, description="Baggage allowance")
    departureAirport: Optional[str] = Field(None, description="Departure airport code")
    arrivalAirport: Optional[str] = Field(None, description="Arrival airport code")
    layovers: Optional[List[LayoverInfo]] = Field(default_factory=list, description="Layover information")


class AccommodationInfo(BaseModel):
    """Accommodation information."""
    id: Optional[str] = Field(None, description="Accommodation ID")
    name: Optional[str] = Field(None, description="Hotel name")
    rating: Optional[float] = Field(None, description="Hotel rating")
    price: Optional[int] = Field(None, description="Base price")
    pricePerNight: Optional[int] = Field(None, description="Price per night")
    totalPrice: Optional[int] = Field(None, description="Total price")
    image: Optional[str] = Field(None, description="Hotel image URL")
    amenities: Optional[List[str]] = Field(default_factory=list, description="Hotel amenities")
    location: Optional[str] = Field(None, description="Hotel location")
    reviews: Optional[int] = Field(None, description="Number of reviews")
    description: Optional[str] = Field(None, description="Hotel description")
    category: Optional[str] = Field(None, description="Hotel category")
    highlights: Optional[List[str]] = Field(default_factory=list, description="Hotel highlights")
    distanceFromCenter: Optional[str] = Field(None, description="Distance from city center")


class TripRequest(BaseModel):
    """Request model for creating a new trip."""
    # Original fields (now optional for backward compatibility)
    destination: Optional[str] = Field(None, description="Trip destination")
    departure_city: Optional[str] = Field(None, description="City of departure", alias="departureCity")
    start_date: Optional[date] = Field(None, description="Trip start date", alias="startDate")
    end_date: Optional[date] = Field(None, description="Trip end date", alias="endDate")
    total_budget: Optional[str] = Field(None, description="Total budget for the trip", alias="totalBudget")
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD)")
    total_adult_travellers: Optional[str] = Field(None, description="Number of adult travelers", alias="totalAdultTravellers")
    total_child_travellers: Optional[int] = Field(None, description="Number of child travelers", alias="totalChildTravellers")
    travelling_with_pets: Optional[bool] = Field(None, description="Whether traveling with pets", alias="travellingWithPets")
    stay_preference: Optional[List[str]] = Field(default_factory=list, description="Accommodation preferences", alias="stayePrefrence")
    transportation_preference: Optional[List[str]] = Field(default_factory=list, description="Transportation preferences", alias="transporationPreference")
    extra_activities: Optional[List[str]] = Field(default_factory=list, description="Extra activities preferences", alias="extraActivites")
    special_requirements: Optional[str] = Field(None, description="Any special requirements", alias="specialRequrements")
    
    # New fields from the enhanced structure
    duration: Optional[int] = Field(None, description="Trip duration in days")
    travelers: Optional[int] = Field(None, description="Number of travelers")
    budgetStatus: Optional[str] = Field(None, description="Budget status")
    daysActivitiesSchedule: Optional[List[DayActivitySchedule]] = Field(default_factory=list, description="Daily activity schedule")
    accommodation: Optional[List[AccommodationInfo]] = Field(default_factory=list, description="Accommodation information")
    flight: Optional[List[FlightInfo]] = Field(default_factory=list, description="Flight information")

    class Config:
        populate_by_name = True


class TripResponse(BaseModel):
    """Response model for trip data."""
    id: str = Field(..., description="Unique trip identifier")
    user_id: str = Field(..., description="User ID who owns this trip")
    destination: Optional[str] = Field(None, description="Trip destination")
    departure_city: Optional[str] = Field(None, description="Departure city")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    total_budget: Optional[str] = Field(None, description="Total budget")
    currency: Optional[str] = Field(None, description="Currency")
    total_adult_travellers: Optional[str] = Field(None, description="Adult travellers")
    total_child_travellers: Optional[int] = Field(None, description="Child travellers")
    travelling_with_pets: Optional[bool] = Field(None, description="Travelling with pets")
    stay_preference: Optional[List[str]] = Field(None, description="Stay preferences")
    transportation_preference: Optional[List[str]] = Field(None, description="Transportation preferences")
    extra_activities: Optional[List[str]] = Field(None, description="Extra activities")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
    created_at: Optional[datetime] = Field(None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp")


class TripCreateResponse(BaseModel):
    """Response model for trip creation."""
    id: str = Field(..., description="Unique trip identifier")
    status: str = Field(default="SAVED", description="Trip status")
    createdAt: str = Field(..., description="Creation timestamp in ISO format")


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
