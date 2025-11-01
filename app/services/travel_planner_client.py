"""API client for connecting to the Travel Planner Service (ADK API)."""

import os
import json
import re
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
from fastapi import HTTPException, status

from app.services.firebase_session_manager import get_firebase_session_manager
from app.parser import get_response_parser


class TravelPlannerClient:
    """Client for communicating with the Travel Planner Service using ADK API endpoints."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("TRAVEL_PLANNER_SERVICE_URL", "http://localhost:8002")
        self.timeout = httpx.Timeout(300.0)  # 5 minutes timeout for long-running requests
        self.app_name = "travel_planner_agent"  # ADK app name
        self.session_manager = get_firebase_session_manager()
        self.response_parser = get_response_parser()
    
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session in both Firebase and ADK service."""
        try:
            # Create session in Firebase
            session_data = self.session_manager.create_session(user_id, session_id)
            
            # Also create session in ADK service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                adk_session_response = await client.post(
                    f"{self.base_url}/apps/{self.app_name}/users/{user_id}/sessions/{session_data['id']}",
                    json={}
                )
                adk_session_response.raise_for_status()
            
            return session_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to create session: {str(e)}"
            )
    
    async def send_message(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send message to travel planner and stream response using ADK run_sse endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # ADK AgentRunRequest format
                request_data = {
                    "appName": self.app_name,
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{"text": message}]
                    },
                    "streaming": True
                }
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/run_sse",
                    json=request_data,
                    headers={"Accept": "text/event-stream"}
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
        """Send message to travel planner and get structured response using ADK run endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # ADK AgentRunRequest format
                request_data = {
                    "appName": self.app_name,
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{"text": message}]
                    },
                    "streaming": False
                }
                
                response = await client.post(
                    f"{self.base_url}/run",
                    json=request_data
                )
                response.raise_for_status()
                events = response.json()
                
                # Use the existing parser to extract structured data
                structured_data = None
                for event in reversed(events):  # Check events in reverse order
                    if event.get("content") and event["content"].get("parts"):
                        for part in event["content"]["parts"]:
                            # Check function responses first (they contain structured data)
                            if part.get("functionResponse"):
                                func_response = part["functionResponse"]
                                if func_response.get("response"):
                                    parsed_data = self.response_parser.parse_adk_content_for_structured_data(
                                        func_response["response"], 
                                        expected_type="hotel"  # Default to hotel for now
                                    )
                                    if parsed_data:
                                        structured_data = parsed_data
                                        break
                            
                            # Check text content for JSON
                            elif part.get("text"):
                                parsed_data = self.response_parser.parse_adk_content_for_structured_data(
                                    part["text"], 
                                    expected_type="hotel"  # Default to hotel for now
                                )
                                if parsed_data:
                                    structured_data = parsed_data
                                    break
                        
                        if structured_data:
                            break
                
                # Extract the data array from the structured response
                extracted_data = structured_data
                if isinstance(structured_data, dict) and "data" in structured_data:
                    if isinstance(structured_data["data"], list):
                        extracted_data = structured_data["data"]
                    elif isinstance(structured_data["data"], dict) and "data" in structured_data["data"]:
                        # Handle nested data structure like {"data": {"data": [...]}}
                        if isinstance(structured_data["data"]["data"], list):
                            extracted_data = structured_data["data"]["data"]
                
                return {
                    "success": True,
                    "data": extracted_data,
                    "message": "Structured data extracted successfully" if extracted_data else "No structured data found"
                }
                
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to get structured response: {str(e)}"
                )
    
    async def get_session_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get current session state using Firebase."""
        try:
            session_data = self.session_manager.get_session(session_id)
            if session_data:
                return session_data
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get session state: {str(e)}"
            )
    
    async def extract_itinerary(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Extract itinerary from session by getting session state."""
        try:
            # Get the session state which contains all the conversation and artifacts
            session_data = await self.get_session_state(user_id, session_id)
            
            # Extract itinerary from session events/artifacts
            # This is a simplified extraction - you might need to customize based on your agent's output format
            events = session_data.get("events", [])
            itinerary_data = None
            
            # Look for itinerary artifacts in the session
            for event in events:
                if event.get("content") and event.get("content").get("parts"):
                    for part in event["content"]["parts"]:
                        if part.get("text") and "itinerary" in part["text"].lower():
                            # Try to parse JSON from the text
                            try:
                                itinerary_data = json.loads(part["text"])
                                break
                            except json.JSONDecodeError:
                                continue
            
            return {
                "success": True,
                "data": itinerary_data,
                "message": "Itinerary extracted from session" if itinerary_data else "No itinerary found in session"
            }
            
        except Exception as e:
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
