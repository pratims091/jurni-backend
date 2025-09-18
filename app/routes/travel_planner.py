"""Travel Planner integration routes for travel-planner-agent communication."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json

from app.auth.middleware import get_current_user
from app.models.user import TokenData
from app.services.firebase_service import get_firebase_service
from app.services.adk_travel_planner_service import get_adk_travel_planner_service

router = APIRouter(prefix="/travel-planner", tags=["travel-planner"])


class ChatRequest(BaseModel):
    """Request for chat with travel planner."""
    message: str
    session_id: Optional[str] = None


class SessionRequest(BaseModel):
    """Request to create/initialize a session."""
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from travel planner chat."""
    success: bool
    message: str
    session_id: str
    data: Optional[Dict[str, Any]] = None


@router.post("/session", response_model=ChatResponse)
async def create_travel_planner_session(
    request: SessionRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create or get a travel planner session initialized with user data.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        firebase_service = get_firebase_service()
        
        # Create/get session
        session_data = await adk_service.create_or_get_session(
            user_id=current_user.uid,
            session_id=request.session_id
        )
        session_id = session_data.get("id")  # ADK returns 'id' not 'session_id'
        
        # Get user data from jurni_backend
        user_profile = firebase_service.get_user_profile(current_user.uid) or {}
        user_profile.update({
            "email": current_user.email,
            "uid": current_user.uid
        })
        
        # Get user's trip history for personalization
        recent_trips = firebase_service.get_user_trips(current_user.uid, limit=10)
        
        # Initialize session with user context
        await adk_service.initialize_session_with_user_data(
            user_id=current_user.uid,
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
    current_user: TokenData = Depends(get_current_user),
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
                print(f"Starting stream for user {current_user.uid}, session {request.session_id}")
                
                # Send initial connection confirmation
                initial_event = {
                    "type": "connection_established",
                    "message": "Connected to travel planner",
                    "session_id": request.session_id
                }
                yield f"data: {json.dumps(initial_event)}\n\n"
                
                async for event in adk_service.send_message(
                    user_id=current_user.uid,
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
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Chat with travel planner and return only structured JSON data.
    This endpoint returns structured data (flights, hotels) instead of streaming all events.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required. Create a session first."
            )
        
        structured_data = None
        data_type = "unknown"
        
        async for event in adk_service.send_message(
            user_id=current_user.uid,
            session_id=request.session_id,
            message=request.message,
            structured_only=True
        ):
            if event.get("type") == "structured_response" and "structured_data" in event:
                structured_data = event["structured_data"]
                data_type = event.get("data_type", "unknown")
                break
        
        if structured_data:
            return {
                "success": True,
                "session_id": request.session_id,
                "data_type": data_type,
                "data": structured_data
            }
        else:
            return {
                "success": False,
                "message": "No structured data found",
                "session_id": request.session_id,
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
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Extract itinerary from travel planner session and save as a trip.
    """
    try:
        adk_service = get_adk_travel_planner_service()
        firebase_service = get_firebase_service()
        
        # Extract itinerary from travel planner session
        trip_data = await adk_service.extract_itinerary_from_session(
            user_id=current_user.uid,
            session_id=session_id
        )
        
        if not trip_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No completed itinerary found in session"
            )
        
        # Save as trip in jurni_backend
        trip_id = firebase_service.save_trip(current_user.uid, trip_data)
        
        if not trip_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save trip"
            )
        
        return ChatResponse(
            success=True,
            message="Itinerary saved as trip successfully",
            session_id=session_id,
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


@router.get("/session/{session_id}/state")
async def get_session_state(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get current state of travel planner session (for debugging/monitoring).
    """
    try:
        adk_service = get_adk_travel_planner_service()
        
        state = await adk_service.get_session_state(
            user_id=current_user.uid,
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
