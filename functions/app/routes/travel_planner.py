"""Travel Planner integration routes for travel-planner-agent communication."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import json

from app.services.firebase_service import get_firebase_service
from app.services.adk_travel_planner_service import get_adk_travel_planner_service

router = APIRouter(prefix="/travel-planner", tags=["travel-planner"])


class ChatRequest(BaseModel):
    """Request for chat with travel planner."""
    user_id: str
    message: str
    session_id: Optional[str] = None


class ActivityItem(BaseModel):
    """Individual activity item for planning."""
    name: str
    description: str
    category: str
    duration: int  # in hours
    cost: int
    rating: float
    popularity: str
    included: bool = False
    difficulty: str
    groupSize: str
    location: str


class StructuredTravelParams(BaseModel):
    """Structured travel parameters for automated queries."""
    destination: str
    departure: str
    budget: str
    currency: str = "INR" 
    totalTravellers: str
    durationDays: str
    startDate: Optional[str] = None
    returnDate: Optional[str] = None
    travelClass: Optional[str] = None
    accommodationType: Optional[str] = None
    # For activity planning - if provided, the agent will organize these activities
    activities: Optional[List[ActivityItem]] = None


class StructuredChatRequest(BaseModel):
    """Request for structured chat with travel planner."""
    user_id: str
    session_id: Optional[str] = None
    query_type: str  # "flights", "hotels", or "itinerary"
    travel_params: StructuredTravelParams


def generate_flight_query_message(params: StructuredTravelParams) -> str:
    """Generate a natural language message for flight search."""
    message = f"I need flights from {params.departure} to {params.destination}"
    
    if params.startDate:
        message += f" on {params.startDate}"
    
    if params.returnDate:
        message += f" returning on {params.returnDate}"
    elif params.durationDays:
        message += f" for {params.durationDays} days"
    
    if params.totalTravellers:
        message += f" for {params.totalTravellers} travelers"
    
    if params.budget and params.currency:
        message += f" with a budget of {params.budget} {params.currency}"
    
    if params.travelClass:
        message += f" in {params.travelClass} class"
    
    return message


def generate_hotel_query_message(params: StructuredTravelParams) -> str:
    """Generate a natural language message for hotel search."""
    message = f"I need hotels in {params.destination}"
    
    if params.durationDays:
        message += f" for {params.durationDays} nights"
    
    if params.totalTravellers:
        message += f" for {params.totalTravellers} guests"
    
    if params.budget and params.currency:
        message += f" with a budget of {params.budget} {params.currency}"
    
    if params.accommodationType:
        message += f" preferring {params.accommodationType} accommodation"
    
    if params.startDate:
        message += f" from {params.startDate}"
    
    return message


def generate_itinerary_query_message(params: StructuredTravelParams) -> str:
    """Generate a natural language message for full itinerary planning."""
    
    # Check if this is activity planning (activities provided) or general itinerary
    if params.activities:
        # Activity planning mode - organize provided activities
        message = f"I have {len(params.activities)} activities that I want to organize into a daily itinerary"
        
        if params.durationDays:
            message += f" across {params.durationDays} days"
        
        if params.totalTravellers:
            message += f" for {params.totalTravellers} travelers"
            
        message += ". Here are the activities:\n\n"
        
        # List all activities with details
        for i, activity in enumerate(params.activities, 1):
            message += f"{i}. {activity.name}\n"
            message += f"   Description: {activity.description}\n"
            message += f"   Category: {activity.category}\n"
            message += f"   Duration: {activity.duration} hours\n"
            message += f"   Cost: {activity.cost}\n"
            message += f"   Difficulty: {activity.difficulty}\n"
            message += f"   Location: {activity.location}\n\n"
        
        message += f"Please use the activity_planning_agent tool to organize these activities into a structured daily itinerary. "
        message += f"Distribute them optimally across the {params.durationDays} days, "
        message += "considering duration, cost, and logistics. "
        message += "I need the result in JSON format showing each day with its activities, "
        message += "daily totals for cost and duration, and grand totals. "
        message += "Make sure to use the activity_planning_agent tool to get the proper JSON structure."
        
    else:
        # General itinerary planning mode
        message = f"I want to plan a trip from {params.departure} to {params.destination}"
        
        if params.durationDays:
            message += f" for {params.durationDays} days"
        
        if params.totalTravellers:
            message += f" for {params.totalTravellers} travelers"
        
        if params.budget and params.currency:
            message += f" with a total budget of {params.budget} {params.currency}"
        
        if params.startDate:
            message += f" starting {params.startDate}"
        
        message += ". Please help me with flights, hotels, and create a complete itinerary."
    
    return message


def generate_activities_query_message(params: StructuredTravelParams) -> str:
    """Generate a natural language message for activities search."""
    message = f"I want to find activities and things to do in {params.destination}"
    
    if params.totalTravellers:
        message += f" for {params.totalTravellers} travelers"
    
    if params.durationDays:
        message += f" during my {params.durationDays} day trip"
    
    if params.budget and params.currency:
        message += f" with a budget of {params.budget} {params.currency}"
    
    message += ". Please provide detailed activity recommendations with costs, duration, and difficulty levels."
    
    return message


class SessionRequest(BaseModel):
    """Request to create/initialize a session."""
    user_id: str
    session_id: Optional[str] = None


class SaveItineraryRequest(BaseModel):
    """Request to save itinerary from session."""
    user_id: str
    session_id: str


class SessionStateRequest(BaseModel):
    """Request to get session state."""
    user_id: str


class ChatResponse(BaseModel):
    """Response from travel planner chat."""
    success: bool
    message: str
    session_id: str
    data: Optional[Dict[str, Any]] = None


@router.post("/session", response_model=ChatResponse)
async def create_travel_planner_session(
    request: SessionRequest,
):
    """
    Create or get a travel planner session initialized with user data.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        firebase_service = get_firebase_service()
        
        # Create/get session
        session_data = await adk_service.create_or_get_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        session_id = session_data.get("id")  # ADK returns 'id' not 'session_id'
        
        # Get user data from jurni_backend
        user_profile = firebase_service.get_user_profile(request.user_id) or {}
        user_profile.update({
            "uid": request.user_id
        })
        
        # Get user's trip history for personalization
        recent_trips = firebase_service.get_user_trips(request.user_id, limit=10)
        
        # Initialize session with user context
        await adk_service.initialize_session_with_user_data(
            user_id=request.user_id,
            session_id=session_id,
            user_profile=user_profile,
            existing_trips=recent_trips
        )
        
        return ChatResponse(
            success=True,
            message="Travel planner session created and initialized",
            session_id=session_id,
            data={"user_trips_count": len(recent_trips)}
        )
        
    except Exception as e:
        print(f"Create travel planner session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create travel planner session"
        )


@router.post("/chat")
async def chat_with_travel_planner(
    request: ChatRequest,
):
    """
    Chat with travel planner and stream responses.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required. Create a session first."
            )
        
        async def generate_events():
            """Stream travel planner events as Server-Sent Events."""
            try:
                print(f"Starting stream for user {request.user_id}, session {request.session_id}")
                
                # Send initial connection confirmation
                initial_event = {
                    "type": "connection_established",
                    "message": "Connected to travel planner",
                    "session_id": request.session_id
                }
                yield f"data: {json.dumps(initial_event)}\n\n"
                
                async for event in adk_service.send_message(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message=request.message
                ):
                    print(f"Forwarding event: {event}")
                    # Forward the event to frontend with proper SSE format
                    yield f"data: {json.dumps(event)}\n\n"
                    
                # Send completion event
                completion_event = {
                    "type": "stream_complete",
                    "message": "Response completed"
                }
                yield f"data: {json.dumps(completion_event)}\n\n"
                
            except Exception as e:
                print(f"Error in generate_events: {e}")
                error_event = {
                    "error": True,
                    "type": "error",
                    "message": str(e),
                    "author": "system"
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Transfer-Encoding": "chunked",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat with travel planner error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to chat with travel planner"
        )


@router.post("/chat-structured")
async def chat_with_travel_planner_structured(
    request: StructuredChatRequest,
):
    """
    Chat with travel planner using structured parameters and return only JSON data.
    
    Query types supported:
    - "flights": Returns flight search results
    - "hotels": Returns hotel search results  
    - "itinerary": Returns complete trip planning OR activity planning (when activities provided)
    - "activities": Returns structured activity recommendations
    
    For Activity Planning:
    - Set query_type to "itinerary" 
    - Include activities array in travel_params
    - The agent will organize your activities into daily itinerary
    - Returns structured daily planning with cost/duration totals
    
    Body should contain travel_params matching your requirements.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required. Create a session first."
            )
        
        # Validate query_type
        valid_query_types = ["flights", "hotels", "itinerary", "activities"]
        if request.query_type not in valid_query_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid query_type. Must be one of: {valid_query_types}"
            )
        
        # Generate appropriate message based on query type
        if request.query_type == "flights":
            generated_message = generate_flight_query_message(request.travel_params)
        elif request.query_type == "hotels":
            generated_message = generate_hotel_query_message(request.travel_params)
        elif request.query_type == "itinerary":
            generated_message = generate_itinerary_query_message(request.travel_params)
        elif request.query_type == "activities":
            generated_message = generate_activities_query_message(request.travel_params)
        
        print(f"Generated message for {request.query_type}: {generated_message}")
        
        # Collect all events to find structured responses
        structured_data = None
        data_type = "unknown"
        
        async for event in adk_service.send_message(
            user_id=request.user_id,
            session_id=request.session_id,
            message=generated_message,
            structured_only=True  # Only get structured responses
        ):
            if event.get("type") == "structured_response" and "structured_data" in event:
                structured_data = event["structured_data"]
                data_type = event.get("data_type", "unknown")
                break
        
        if structured_data:
            return {
                "success": True,
                "message": f"{request.query_type.title()} data retrieved successfully",
                "session_id": request.session_id,
                "query_type": request.query_type,
                "data_type": data_type,
                "generated_query": generated_message,
                "data": structured_data
            }
        else:
            return {
                "success": False,
                "message": f"No structured {request.query_type} data found",
                "session_id": request.session_id,
                "query_type": request.query_type,
                "generated_query": generated_message,
                "data": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat structured error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get structured data from travel planner"
        )
@router.post("/save-itinerary")
async def save_itinerary_to_trip(
    request: SaveItineraryRequest,
):
    """
    Extract itinerary from travel planner session and save as a trip.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        firebase_service = get_firebase_service()
        
        # Extract itinerary from travel planner session
        trip_data = await adk_service.extract_itinerary_from_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        if not trip_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No completed itinerary found in session"
            )
        
        # Save as trip in jurni_backend
        trip_id = firebase_service.save_trip(request.user_id, trip_data)
        
        if not trip_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save trip"
            )
        
        return ChatResponse(
            success=True,
            message="Itinerary saved as trip successfully",
            session_id=request.session_id,
            data={"trip_id": trip_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Save itinerary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save itinerary"
        )


@router.post("/session/{session_id}/state")
async def get_session_state(
    session_id: str,
    request: SessionStateRequest,
):
    """
    Get current state of travel planner session (for debugging/monitoring).
    """
    try:
        adk_service = get_adk_travel_planner_service()
        
        state = await adk_service.get_session_state(
            user_id=request.user_id,
            session_id=session_id
        )
        
        return ChatResponse(
            success=True,
            message="Session state retrieved",
            session_id=session_id,
            data=state
        )
        
    except Exception as e:
        print(f"Get session state error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session state"
        )
