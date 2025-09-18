"""Direct ADK integration service for travel-planner-agent agents."""

import os
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import Session, InMemorySessionService
from google.adk.events import Event
from google.genai.types import Content, Part
import base64

from app.travel_planner_agent.agent import root_agent


class ADKTravelPlannerService:
    """Direct ADK integration service for travel-planner-agent agents."""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.runners: Dict[str, Runner] = {}
        self.session_service = InMemorySessionService()
        # Single runner instance that will handle all sessions
        self.runner = Runner(
            app_name="travel_planner_agent",
            agent=root_agent,
            session_service=self.session_service
        )
    
    async def create_or_get_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create or retrieve a session for the user."""
        if not session_id:
            session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        if session_id not in self.sessions:
            # Create session using the session service
            session = await self.session_service.create_session(
                app_name="travel_planner_agent",
                user_id=user_id,
                session_id=session_id
            )
            
            # Store session in our local dict for quick access
            self.sessions[session_id] = session
        
        return {
            "id": session_id,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    
    async def initialize_session_with_user_data(
        self, 
        user_id: str, 
        session_id: str, 
        user_profile: Dict[str, Any],
        existing_trips: list = None
    ) -> Dict[str, Any]:
        """Initialize session with user data from jurni_backend."""
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # Prepare user context for travel-planner-agent
        user_context = {
            "user_profile": {
                "email": user_profile.get("email"),
                "display_name": user_profile.get("display_name", user_profile.get("first_name", "")),
                "first_name": user_profile.get("first_name", ""),
                "last_name": user_profile.get("last_name", ""),
                "passport_nationality": user_profile.get("passport_nationality", "US"),
                "home": {
                    "address": user_profile.get("address", "Default Address"),
                    "local_prefer_mode": user_profile.get("preferred_transport", "driving")
                },
                "preferences": {
                    "previous_trips": existing_trips or [],
                    "travel_style": user_profile.get("travel_style", "adventure"),
                    "budget_range": user_profile.get("budget_range", "moderate"),
                }
            },
            "itinerary": {},  # Empty itinerary to start
            "system_time": datetime.now().isoformat()
        }
        
        # Set user context in session state
        for key, value in user_context.items():
            session.state[key] = value
        
        return {"status": "initialized", "user_context": user_context}
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str,
        structured_only: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send message to travel-planner-agent and stream response events."""
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        try:
            # Run the agent with the message and collect events
            # Format the message according to ADK requirements
            new_message = Content(
                role="user",
                parts=[Part(text=message)]
            )
            
            events = []
            structured_data_found = None
            
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id, 
                new_message=new_message
            ):
                # Convert ADK event to our format
                event_dict = self._convert_adk_event_to_dict(event)
                events.append(event_dict)
                
                # Check if this is structured data
                if event_dict.get("type") == "structured_response" and "structured_data" in event_dict:
                    structured_data_found = event_dict
                
                # If structured_only is True, only yield structured responses
                if structured_only:
                    if event_dict.get("type") == "structured_response":
                        yield event_dict
                else:
                    yield event_dict
                
            # Handle structured_only mode - if we found structured data but haven't yielded it yet
            if structured_only and structured_data_found:
                yield structured_data_found
                return
                    
            # If no events were yielded, ensure we return at least a response
            if not events:
                # Get the latest event from session
                latest_event = session.events[-1] if session.events else None
                if latest_event and hasattr(latest_event, 'content'):
                    # Convert content to JSON-serializable format
                    content = latest_event.content
                    if hasattr(content, 'model_dump'):
                        content = content.model_dump()
                    elif hasattr(content, 'dict'):
                        content = content.dict()
                    else:
                        content = str(content)
                    
                    response_event = {
                        "type": "agent_message",
                        "author": "root_agent",
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield response_event
                    
        except Exception as e:
            error_event = {
                "type": "error",
                "error": True,
                "message": f"Agent execution error: {str(e)}",
                "author": "system",
                "timestamp": datetime.now().isoformat()
            }
            yield error_event
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert any object to JSON serializable format."""
        try:
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, bytes):
                # Convert bytes to base64 string
                return base64.b64encode(obj).decode('utf-8')
            elif isinstance(obj, (list, tuple)):
                return [self._make_json_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: self._make_json_serializable(value) for key, value in obj.items()}
            elif hasattr(obj, 'model_dump'):
                return self._make_json_serializable(obj.model_dump())
            elif hasattr(obj, 'dict'):
                return self._make_json_serializable(obj.dict())
            elif hasattr(obj, '__dict__'):
                return self._make_json_serializable(obj.__dict__)
            else:
                # Fallback: convert to string
                return str(obj)
        except Exception as e:
            print(f"Error making object JSON serializable: {e}, object: {type(obj)}")
            return str(obj)
    
    def _is_json_string(self, text: str) -> bool:
        """Check if a string is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _check_for_structured_data(self, content: Any, event_dict: Dict[str, Any]) -> None:
        """Check content for structured JSON data and update event dict accordingly."""
        # Check if content is already structured (from output_schema)
        if isinstance(content, dict) and "data" in content:
            # Direct structured data from agent output schema
            event_dict["structured_data"] = content
            event_dict["type"] = "structured_response"
            
            # Detect data type
            data_items = content.get("data", [])
            if data_items and isinstance(data_items, list) and len(data_items) > 0:
                first_item = data_items[0]
                if isinstance(first_item, dict):
                    if "flightNumber" in first_item:
                        event_dict["data_type"] = "flights"
                    elif "pricePerNight" in first_item:
                        event_dict["data_type"] = "hotels"
            return
        
        # Check for JSON strings in text parts
        if isinstance(content, dict) and 'parts' in content:
            for part in content.get('parts', []):
                if isinstance(part, dict) and 'text' in part:
                    text_content = part['text']
                    if isinstance(text_content, str) and self._is_json_string(text_content):
                        try:
                            # Parse the JSON and add it as structured_data
                            structured_data = json.loads(text_content)
                            if "data" in structured_data:
                                event_dict["structured_data"] = structured_data
                                event_dict["type"] = "structured_response"
                                # Also detect specific data types
                                data_items = structured_data.get("data", [])
                                if data_items and isinstance(data_items, list) and len(data_items) > 0:
                                    first_item = data_items[0]
                                    if isinstance(first_item, dict):
                                        if "flightNumber" in first_item:
                                            event_dict["data_type"] = "flights"
                                        elif "pricePerNight" in first_item:
                                            event_dict["data_type"] = "hotels"
                        except json.JSONDecodeError:
                            continue
    
    def _convert_adk_event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert ADK Event to dictionary format expected by frontend."""
        
        # Start with basic event info
        event_dict = {
            "timestamp": datetime.now().isoformat(),
            "author": "system",  # default
            "type": "agent_message"  # default
        }
        
        # Safely get basic properties
        try:
            if hasattr(event, 'author') and event.author:
                event_dict["author"] = event.author
            
            if hasattr(event, 'timestamp') and event.timestamp:
                event_dict["timestamp"] = event.timestamp
                
            # Add content if available
            if hasattr(event, 'content') and event.content:
                # Convert Content object to JSON-serializable dict
                content = self._make_json_serializable(event.content)
                event_dict["content"] = content
                
                # Check if the content contains structured JSON data
                self._check_for_structured_data(content, event_dict)
        except Exception as e:
            print(f"Error getting basic event properties: {e}")
        
        # Safely determine event type and add specific data
        try:
            # Check for function calls
            function_calls = event.get_function_calls()
            if function_calls:
                event_dict["function_calls"] = self._make_json_serializable(function_calls)
                event_dict["type"] = "function_call"
        except Exception as e:
            print(f"Error getting function calls: {e}")
        
        try:
            # Check for function responses
            function_responses = event.get_function_responses()
            if function_responses:
                event_dict["function_responses"] = self._make_json_serializable(function_responses)
                event_dict["type"] = "function_response"
                
                # Check if function responses contain structured data
                responses_serialized = self._make_json_serializable(function_responses)
                for response in responses_serialized:
                    if isinstance(response, dict) and 'response' in response:
                        response_data = response['response']
                        if isinstance(response_data, dict) and 'data' in response_data:
                            # This looks like our structured data format
                            event_dict["structured_data"] = response_data
                            event_dict["type"] = "structured_response"
                            
                            # Detect data type
                            data_items = response_data.get("data", [])
                            if data_items and isinstance(data_items, list) and len(data_items) > 0:
                                first_item = data_items[0]
                                if isinstance(first_item, dict):
                                    if "flightNumber" in first_item:
                                        event_dict["data_type"] = "flights"
                                    elif "pricePerNight" in first_item:
                                        event_dict["data_type"] = "hotels"
        except Exception as e:
            print(f"Error getting function responses: {e}")
        
        try:
            # Check if it's a final response
            if event.is_final_response():
                event_dict["type"] = "final_response"
                event_dict["final"] = True
        except Exception as e:
            print(f"Error checking if final response: {e}")
        
        # Handle errors
        try:
            if hasattr(event, 'error_message') and event.error_message:
                event_dict["error"] = True
                event_dict["message"] = event.error_message
                event_dict["type"] = "error"
        except Exception as e:
            print(f"Error handling error message: {e}")
        
        # Add additional metadata safely
        try:
            if hasattr(event, 'partial') and event.partial:
                event_dict["partial"] = True
            
            if hasattr(event, 'turn_complete') and event.turn_complete:
                event_dict["turn_complete"] = True
        except Exception as e:
            print(f"Error getting metadata: {e}")
        
        # Make the entire event dict JSON serializable as a final pass
        return self._make_json_serializable(event_dict)
    
    async def get_session_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get current session state (includes itinerary, preferences, etc.)."""
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "state": dict(session.state),
            "status": "active",
            "message_count": len(session.events)
        }
    
    async def extract_itinerary_from_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Extract completed itinerary from session state."""
        
        state_data = await self.get_session_state(user_id, session_id)
        
        # The travel-planner-agent stores itinerary in session state
        itinerary = state_data.get("state", {}).get("itinerary", {})
        
        if itinerary and itinerary.get("days"):
            # Convert ADK itinerary format to jurni_backend trip format
            return self._convert_itinerary_to_trip_data(itinerary)
        
        return None
    
    def _convert_itinerary_to_trip_data(self, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        """Convert travel-planner-agent itinerary to jurni_backend trip format."""
        
        # Extract basic trip information
        trip_data = {
            "destination": itinerary.get("destination", ""),
            "departure_city": itinerary.get("origin", ""),
            "start_date": itinerary.get("start_date", ""),
            "end_date": itinerary.get("end_date", ""),
            "total_budget": str(itinerary.get("estimated_budget", 0)),
            "currency": "USD",
            "total_adult_travellers": str(itinerary.get("travelers", {}).get("adults", 1)),
            "total_child_travellers": itinerary.get("travelers", {}).get("children", 0),
            "travelling_with_pets": itinerary.get("travelers", {}).get("pets", False),
            "stay_preference": [],
            "transportation_preference": [],
            "extra_activities": [],
            "special_requirements": itinerary.get("notes", "")
        }
        
        # Extract preferences from itinerary days/events
        days = itinerary.get("days", [])
        if days:
            # Analyze events to extract preferences
            for day in days:
                events = day.get("events", [])
                for event in events:
                    event_type = event.get("event_type", "")
                    if event_type == "hotel":
                        room_type = event.get("room_selection", "")
                        if room_type and room_type not in trip_data["stay_preference"]:
                            trip_data["stay_preference"].append(room_type)
                    elif event_type == "visit":
                        activity = event.get("description", "")
                        if activity and activity not in trip_data["extra_activities"]:
                            trip_data["extra_activities"].append(activity)
                    elif event_type == "transportation":
                        transport = event.get("type", "")
                        if transport and transport not in trip_data["transportation_preference"]:
                            trip_data["transportation_preference"].append(transport)
        
        return trip_data
    
    def cleanup_session(self, session_id: str):
        """Clean up session resources."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.runners:
            del self.runners[session_id]


# Global instance
_adk_travel_planner_service = None

def get_adk_travel_planner_service() -> ADKTravelPlannerService:
    """Get the global ADK travel planner service instance."""
    global _adk_travel_planner_service
    if _adk_travel_planner_service is None:
        _adk_travel_planner_service = ADKTravelPlannerService()
    return _adk_travel_planner_service
