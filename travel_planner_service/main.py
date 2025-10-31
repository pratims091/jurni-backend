"""Travel Planner Service - Standalone FastAPI service for travel planning."""

import os
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

from travel_planner_agent.agent import root_agent
from adk_service import ADKTravelPlannerService

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 Travel Planner Service starting up...")
    yield
    print("🛑 Travel Planner Service shutting down...")


app = FastAPI(
    title="Travel Planner Service",
    description="Standalone travel planning service using Google ADK",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionRequest(BaseModel):
    """Request to create/initialize a session."""
    user_id: str
    session_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat with travel planner."""
    user_id: str
    message: str
    session_id: str


class UserContextRequest(BaseModel):
    """Request to initialize session with user data."""
    user_id: str
    session_id: str
    user_profile: Dict[str, Any]
    existing_trips: Optional[list] = None


class SessionStateRequest(BaseModel):
    """Request to get session state."""
    user_id: str
    session_id: str


class ChatResponse(BaseModel):
    """Response from travel planner chat."""
    success: bool
    message: str
    session_id: str
    data: Optional[Dict[str, Any]] = None


# Global service instance
adk_service = ADKTravelPlannerService()


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Travel Planner Service is running",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/session", response_model=ChatResponse)
async def create_session(request: SessionRequest):
    """Create or get a travel planner session."""
    try:
        session_data = await adk_service.create_or_get_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        session_id = session_data.get("id")
        
        return ChatResponse(
            success=True,
            message="Travel planner session created",
            session_id=session_id,
            data=session_data
        )
        
    except Exception as e:
        print(f"Create session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create travel planner session"
        )


@app.post("/session/initialize")
async def initialize_session_with_user_data(request: UserContextRequest):
    """Initialize session with user data."""
    try:
        result = await adk_service.initialize_session_with_user_data(
            user_id=request.user_id,
            session_id=request.session_id,
            user_profile=request.user_profile,
            existing_trips=request.existing_trips
        )
        
        return ChatResponse(
            success=True,
            message="Session initialized with user data",
            session_id=request.session_id,
            data=result
        )
        
    except Exception as e:
        print(f"Initialize session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize session with user data"
        )


@app.post("/chat")
async def chat_with_travel_planner(request: ChatRequest):
    """Chat with travel planner and stream responses."""
    try:
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
        
    except Exception as e:
        print(f"Chat with travel planner error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to chat with travel planner"
        )


@app.post("/chat/structured")
async def chat_structured(request: ChatRequest):
    """Chat with travel planner and return only structured data."""
    try:
        structured_data = None
        data_type = "unknown"
        
        async for event in adk_service.send_message(
            user_id=request.user_id,
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
                "message": "Structured data retrieved successfully",
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
        
    except Exception as e:
        print(f"Chat structured error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get structured data from travel planner"
        )


@app.post("/session/{session_id}/state")
async def get_session_state(session_id: str, request: SessionStateRequest):
    """Get current state of travel planner session."""
    try:
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


@app.post("/session/{session_id}/extract-itinerary")
async def extract_itinerary(session_id: str, request: SessionStateRequest):
    """Extract completed itinerary from session."""
    try:
        itinerary = await adk_service.extract_itinerary_from_session(
            user_id=request.user_id,
            session_id=session_id
        )
        
        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No completed itinerary found in session"
            )
        
        return ChatResponse(
            success=True,
            message="Itinerary extracted successfully",
            session_id=session_id,
            data=itinerary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Extract itinerary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract itinerary"
        )


if __name__ == "__main__":
    port = int(os.getenv("TRAVEL_PLANNER_PORT", 8002))
    host = os.getenv("TRAVEL_PLANNER_HOST", "0.0.0.0")
    
    uvicorn.run(
        "travel_planner_service.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
