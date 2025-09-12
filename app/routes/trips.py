"""Trip routes for creating and managing trips."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, date
from typing import Optional
from app.models.trip import TripRequest, TripCreateResponse, TripResponse, TripListResponse, TripSummary
from app.auth.middleware import get_current_user
from app.models.user import TokenData
from app.services.firebase_service import get_firebase_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=TripCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripRequest, current_user: TokenData = Depends(get_current_user)):
    """
    Create a new trip for the authenticated user.
    """
    try:
        firebase_service = get_firebase_service()

        trip_data = {
            "destination": trip.destination,
            "departure_city": trip.departure_city,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "total_budget": trip.total_budget,
            "currency": trip.currency,
            "total_adult_travellers": trip.total_adult_travellers,
            "total_child_travellers": trip.total_child_travellers,
            "travelling_with_pets": trip.travelling_with_pets,
            "stay_preference": trip.stay_preference,
            "transportation_preference": trip.transportation_preference,
            "extra_activities": trip.extra_activities,
            "special_requirements": trip.special_requirements,
        }

        trip_id = firebase_service.save_trip(current_user.uid, trip_data)
        if not trip_id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save trip")

        now = datetime.utcnow()
        trip_resp = TripResponse(
            id=trip_id,
            user_id=current_user.uid,
            destination=trip.destination,
            departure_city=trip.departure_city,
            start_date=trip.start_date,
            end_date=trip.end_date,
            total_budget=trip.total_budget,
            currency=trip.currency,
            total_adult_travellers=trip.total_adult_travellers,
            total_child_travellers=trip.total_child_travellers,
            travelling_with_pets=trip.travelling_with_pets,
            stay_preference=trip.stay_preference,
            transportation_preference=trip.transportation_preference,
            extra_activities=trip.extra_activities,
            special_requirements=trip.special_requirements,
            created_at=now,
            updated_at=now,
        )

        return TripCreateResponse(success=True, message="Trip created successfully", trip=trip_resp)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create trip error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the trip")


@router.get("/", response_model=TripListResponse)
async def list_trips(
    limit: int = Query(20, ge=1, le=100, description="Max number of trips to return"),
    offset: int = Query(0, ge=0, description="Number of trips to skip for pagination"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get all trips for the authenticated user.
    """
    try:
        firebase_service = get_firebase_service()
        trips_data = firebase_service.get_user_trips(current_user.uid, limit=limit, offset=offset)

        trips: list[TripSummary] = []
        for trip in trips_data:
            trips.append(
                TripSummary(
                    id=trip.get("id"),
                    created_at=trip.get("created_at"),
                    destination=trip.get("destination"),
                    departure_city=trip.get("departure_city"),
                )
            )

        return TripListResponse(
            success=True, 
            message="Trips fetched successfully", 
            trips=trips, 
            total_count=len(trips)
        )
    except Exception as e:
        print(f"List trips error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to fetch trips"
        )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip_by_id(
    trip_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get a specific trip by ID for the authenticated user.
    Returns all trip details if the trip belongs to the user.
    """
    try:
        firebase_service = get_firebase_service()
        trip_data = firebase_service.get_trip(trip_id, current_user.uid)
        
        if not trip_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or you don't have permission to access it"
            )
        
        trip_response = TripResponse(
            id=trip_data.get("id"),
            user_id=trip_data.get("user_id"),
            destination=trip_data.get("destination"),
            departure_city=trip_data.get("departure_city"),
            start_date=date.fromisoformat(trip_data.get("start_date")),
            end_date=date.fromisoformat(trip_data.get("end_date")),
            total_budget=trip_data.get("total_budget"),
            currency=trip_data.get("currency"),
            total_adult_travellers=trip_data.get("total_adult_travellers"),
            total_child_travellers=trip_data.get("total_child_travellers", 0),
            travelling_with_pets=trip_data.get("travelling_with_pets", False),
            stay_preference=trip_data.get("stay_preference", []),
            transportation_preference=trip_data.get("transportation_preference", []),
            extra_activities=trip_data.get("extra_activities", []),
            special_requirements=trip_data.get("special_requirements", ""),
            created_at=trip_data.get("created_at"),
            updated_at=trip_data.get("updated_at"),
        )
        
        return trip_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get trip by ID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trip details"
        )

