"""Trip routes for creating and managing trips."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, date
from typing import Optional
from app.models.trip import TripRequest, TripCreateResponse
from app.auth.middleware import get_current_user
from app.models.user import TokenData
from app.services.firebase_service import get_firebase_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=TripCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripRequest, current_user: TokenData = Depends(get_current_user)):
    """
    Create a new trip for the authenticated user.
    Supports both original trip format and new enhanced format with activities, accommodation, and flights.
    """
    try:
        firebase_service = get_firebase_service()

        # Build trip data dictionary - handle both old and new formats
        trip_data = {}
        
        # Original fields (maintain backward compatibility)
        if trip.destination:
            trip_data["destination"] = trip.destination
        if trip.departure_city:
            trip_data["departure_city"] = trip.departure_city
        if trip.start_date:
            trip_data["start_date"] = trip.start_date.isoformat()
        if trip.end_date:
            trip_data["end_date"] = trip.end_date.isoformat()
        if trip.total_budget:
            trip_data["total_budget"] = trip.total_budget
        if trip.currency:
            trip_data["currency"] = trip.currency
        if trip.total_adult_travellers:
            trip_data["total_adult_travellers"] = trip.total_adult_travellers
        if trip.total_child_travellers is not None:
            trip_data["total_child_travellers"] = trip.total_child_travellers
        if trip.travelling_with_pets is not None:
            trip_data["travelling_with_pets"] = trip.travelling_with_pets
        if trip.stay_preference:
            trip_data["stay_preference"] = trip.stay_preference
        if trip.transportation_preference:
            trip_data["transportation_preference"] = trip.transportation_preference
        if trip.extra_activities:
            trip_data["extra_activities"] = trip.extra_activities
        if trip.special_requirements:
            trip_data["special_requirements"] = trip.special_requirements
            
        # New enhanced fields
        if trip.duration is not None:
            trip_data["duration"] = trip.duration
        if trip.travelers is not None:
            trip_data["travelers"] = trip.travelers
        if trip.budgetStatus:
            trip_data["budgetStatus"] = trip.budgetStatus
        if trip.daysActivitiesSchedule:
            trip_data["daysActivitiesSchedule"] = [schedule.model_dump() for schedule in trip.daysActivitiesSchedule]
        if trip.accommodation:
            trip_data["accommodation"] = [acc.model_dump() for acc in trip.accommodation]
        if trip.flight:
            trip_data["flight"] = [flight.model_dump() for flight in trip.flight]

        trip_id = firebase_service.save_trip(current_user.uid, trip_data)
        if not trip_id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save trip")

        # Return the expected response format
        now = datetime.utcnow()
        return TripCreateResponse(
            id=trip_id,
            status="SAVED",
            createdAt=now.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create trip error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the trip")


@router.get("/")
async def list_trips(
    limit: int = Query(20, ge=1, le=100, description="Max number of trips to return"),
    offset: int = Query(0, ge=0, description="Number of trips to skip for pagination"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get all trips for the authenticated user.
    Returns raw trip data from database without validation, with pagination support.
    """
    try:
        firebase_service = get_firebase_service()
        trips_data = firebase_service.get_user_trips(current_user.uid, limit=limit, offset=offset)

        # Return raw data from database without any transformation
        return {
            "trips": trips_data,
            "total_count": len(trips_data),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"List trips error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to fetch trips"
        )


@router.get("/{trip_id}")
async def get_trip_by_id(
    trip_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get a specific trip by ID for the authenticated user.
    Returns raw trip data from database without validation.
    """
    try:
        firebase_service = get_firebase_service()
        trip_data = firebase_service.get_trip(trip_id, current_user.uid)
        
        if not trip_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or you don't have permission to access it"
            )
        
        # Return raw data from database without any transformation
        return trip_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get trip by ID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trip details"
        )

