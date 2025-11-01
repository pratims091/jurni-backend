"""API client for connecting to the Travel Planner Service."""

import os
import json
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
from fastapi import HTTPException, status


class TravelPlannerClient:
    """Client for communicating with the Travel Planner Service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("TRAVEL_PLANNER_SERVICE_URL", "http://localhost:8002")
        self.timeout = httpx.Timeout(300.0)  # 5 minutes timeout for long-running requests
    
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session with the travel planner service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/session",
                    json={
                        "user_id": user_id,
                        "session_id": session_id
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Travel planner service unavailable: {str(e)}"
                )
    
    async def initialize_session_with_user_data(
        self,
        user_id: str,
        session_id: str,
        user_profile: Dict[str, Any],
        existing_trips: list = None
    ) -> Dict[str, Any]:
        """Initialize session with user data."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/session/initialize",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_profile": user_profile,
                        "existing_trips": existing_trips or []
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to initialize session: {str(e)}"
                )
    
    async def send_message(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send message to travel planner and stream response."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "message": message
                    }
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])  # Remove "data: " prefix
                                yield event_data
                            except json.JSONDecodeError:
                                continue
                                
            except httpx.HTTPError as e:
                error_event = {
                    "type": "error",
                    "error": True,
                    "message": f"Travel planner service error: {str(e)}",
                    "author": "system"
                }
                yield error_event
    
    async def send_message_structured(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Send message to travel planner and get structured response."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/structured",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "message": message
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to get structured response: {str(e)}"
                )
    
    async def get_session_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get current session state."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/session/{session_id}/state",
                    json={
                        "user_id": user_id,
                        "session_id": session_id
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to get session state: {str(e)}"
                )
    
    async def extract_itinerary(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Extract itinerary from session."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/session/{session_id}/extract-itinerary",
                    json={
                        "user_id": user_id,
                        "session_id": session_id
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to extract itinerary: {str(e)}"
                )


# Global instance
_travel_planner_client = None


def get_travel_planner_client() -> TravelPlannerClient:
    """Get the global travel planner client instance."""
    global _travel_planner_client
    if _travel_planner_client is None:
        _travel_planner_client = TravelPlannerClient()
    return _travel_planner_client
