"""Enhanced response parser for structured data from ADK agents."""

import json
import re
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from app.services.flight_service import get_flight_service


class StructuredResponseParser:
    """Parser to detect and format structured responses from ADK agents."""
    
    def __init__(self):
        self.flight_service = get_flight_service()
        
        # Keywords that indicate structured data requests
        self.flight_keywords = [
            "flight", "flights", "fly", "flying", "airline", "airplane", "book flight", 
            "flight search", "flight deals", "airfare", "plane ticket"
        ]
        self.hotel_keywords = [
            "hotel", "hotels", "accommodation", "stay", "room", "booking", "lodge", "resort"
        ]
        self.itinerary_keywords = [
            "itinerary", "plan", "schedule", "trip plan", "travel plan", "day by day"
        ]
    
    def should_return_structured_data(self, message: str, agent_name: str = None) -> str:
        """
        Determine if the response should be structured data based on message content and agent.
        Returns the type of structured data expected: 'flight', 'hotel', 'itinerary', or None.
        """
        message_lower = message.lower()
        
        # Check if this is a flight-related request
        if any(keyword in message_lower for keyword in self.flight_keywords):
            return "flight"
        
        # Check if this is a hotel-related request  
        if any(keyword in message_lower for keyword in self.hotel_keywords):
            return "hotel"
            
        # Check if this is an itinerary request
        if any(keyword in message_lower for keyword in self.itinerary_keywords):
            return "itinerary"
        
        # Check agent name for additional context
        if agent_name:
            agent_lower = agent_name.lower()
            if "flight" in agent_lower:
                return "flight"
            elif "hotel" in agent_lower:
                return "hotel"
            elif "itinerary" in agent_lower:
                return "itinerary"
        
        return None
    
    def extract_search_criteria_from_message(self, message: str) -> Dict[str, Any]:
        """Extract search criteria from user message using regex and keywords."""
        criteria = {}
        message_lower = message.lower()
        
        # Extract cities/airports (look for common patterns)
        # Pattern: "from X to Y" - more specific to avoid capturing other words
        patterns = [
            r'(?:from|leave|depart)\s+([A-Za-z][A-Za-z\s]{2,15})\s+(?:to|for|arrive|land)\s+([A-Za-z][A-Za-z\s]{2,15})',
            r'([A-Za-z][A-Za-z\s]{2,15})\s+(?:to|-)\s+([A-Za-z][A-Za-z\s]{2,15})(?:\s+flight|\s+trip|\s*$)',
        ]
        
        for pattern in patterns:
            city_match = re.search(pattern, message_lower)
            if city_match:
                origin = city_match.group(1).strip().title()
                destination = city_match.group(2).strip().title()
                # Filter out common non-city words
                non_cities = ['flight', 'flights', 'book', 'find', 'need', 'want', 'show', 'get']
                if (origin.lower() not in non_cities and destination.lower() not in non_cities and
                    len(origin) >= 3 and len(destination) >= 3):
                    criteria['origin'] = origin
                    criteria['destination'] = destination
                    break
        
        # Extract dates (look for various date formats)
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # MM/DD/YYYY or M/D/YYYY
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,\s*\d{4})?\b'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, message_lower)
            if date_match:
                criteria['departure_date'] = date_match.group(1)
                break
        
        # Extract passenger count
        passenger_pattern = r'\b(\d+)\s+(?:passenger|person|people|traveler|adult)s?\b'
        passenger_match = re.search(passenger_pattern, message_lower)
        if passenger_match:
            criteria['passenger_count'] = int(passenger_match.group(1))
        
        # Extract class preference
        if any(term in message_lower for term in ['business', 'first class', 'premium']):
            criteria['class'] = 'business'
        elif 'economy' in message_lower:
            criteria['class'] = 'economy'
        
        return criteria
    
    def parse_adk_content_for_structured_data(self, content: Any, expected_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Parse ADK agent content to extract structured data.
        
        Args:
            content: The content from ADK event
            expected_type: Expected type of structured data ('flight', 'hotel', 'itinerary')
        
        Returns:
            Structured data dictionary or None if no structured data found
        """
        if not content:
            return None
        
        # If content is already a dict with structured data
        if isinstance(content, dict):
            # Check for flight data structures
            if expected_type == "flight" or self._contains_flight_data(content):
                return self._format_flight_response(content)
            
            # Check for hotel data structures
            elif expected_type == "hotel" or self._contains_hotel_data(content):
                return self._format_hotel_response(content)
            
            # Check for itinerary data structures
            elif expected_type == "itinerary" or self._contains_itinerary_data(content):
                return self._format_itinerary_response(content)
        
        # If content is a string, try to parse JSON
        elif isinstance(content, str):
            try:
                parsed_content = json.loads(content)
                return self.parse_adk_content_for_structured_data(parsed_content, expected_type)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def generate_mock_flight_response(self, search_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a mock flight response using the flight service."""
        if not search_criteria:
            search_criteria = {}
        
        return self.flight_service.search_flights(
            origin=search_criteria.get('origin'),
            destination=search_criteria.get('destination'),
            departure_date=search_criteria.get('departure_date'),
            passenger_count=search_criteria.get('passenger_count', 1),
            flight_class=search_criteria.get('class', 'economy')
        )
    
    def _contains_flight_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains flight-related structure."""
        flight_indicators = [
            'flights', 'flight_number', 'departure', 'arrival', 'airline', 'price_in_usd'
        ]
        return any(indicator in str(data).lower() for indicator in flight_indicators)
    
    def _contains_hotel_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains hotel-related structure.""" 
        hotel_indicators = [
            'hotels', 'hotel', 'check_in', 'check_out', 'room_type', 'rooms'
        ]
        return any(indicator in str(data).lower() for indicator in hotel_indicators)
    
    def _contains_itinerary_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains itinerary-related structure."""
        itinerary_indicators = [
            'itinerary', 'days', 'day_number', 'trip_name', 'start_date', 'end_date'
        ]
        return any(indicator in str(data).lower() for indicator in itinerary_indicators)
    
    def _format_flight_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format flight data into expected frontend structure."""
        return {
            "type": "flight_search_results",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_hotel_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format hotel data into expected frontend structure."""
        return {
            "type": "hotel_search_results", 
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_itinerary_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format itinerary data into expected frontend structure."""
        return {
            "type": "itinerary_results",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
_response_parser = None

def get_response_parser() -> StructuredResponseParser:
    """Get the global response parser instance."""
    global _response_parser
    if _response_parser is None:
        _response_parser = StructuredResponseParser()
    return _response_parser