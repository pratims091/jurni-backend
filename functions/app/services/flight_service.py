"""Flight service for providing structured flight data."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pathlib import Path


class FlightService:
    """Service for flight search and data management."""
    
    def __init__(self):
        self.flights_data_path = Path(__file__).parent.parent.parent / "flights.json"
        self._load_flight_data()
    
    def _load_flight_data(self):
        """Load flight data from flights.json file."""
        try:
            if self.flights_data_path.exists():
                with open(self.flights_data_path, 'r') as f:
                    self.flights_data = json.load(f)
            else:
                # Default flight data if file doesn't exist
                self.flights_data = {
                    "data": [
                        {
                            "id": "economy1",
                            "airline": "Budget Wings",
                            "flightNumber": "BW-5432",
                            "price": 8500,
                            "duration": "4h 30m",
                            "departure": "08:15",
                            "arrival": "13:45",
                            "departureDate": "2024-01-15",
                            "arrivalDate": "2024-01-15",
                            "stops": 1,
                            "aircraft": "Boeing 737",
                            "class": "economy",
                            "amenities": ["Snacks"],
                            "baggage": "15kg checked + 7kg cabin",
                            "departureAirport": "DEL",
                            "arrivalAirport": "GOI",
                            "layovers": [{"city": "Mumbai", "duration": "1h 20m"}]
                        }
                    ]
                }
        except Exception as e:
            print(f"Error loading flight data: {e}")
            self.flights_data = {"data": []}
    
    def search_flights(
        self, 
        origin: str = None, 
        destination: str = None, 
        departure_date: str = None,
        passenger_count: int = 1,
        flight_class: str = "economy"
    ) -> Dict[str, Any]:
        """
        Search for flights based on criteria.
        Returns structured flight data in the format expected by frontend.
        """
        # For now, return the mock data with some customization
        flights = []
        
        for flight_data in self.flights_data.get("data", []):
            # Customize the flight data based on search criteria
            customized_flight = flight_data.copy()
            
            if origin:
                customized_flight["departureAirport"] = origin
            if destination:
                customized_flight["arrivalAirport"] = destination
            if departure_date:
                customized_flight["departureDate"] = departure_date
                customized_flight["arrivalDate"] = departure_date
            if flight_class:
                customized_flight["class"] = flight_class
            
            flights.append(customized_flight)
        
        return {
            "type": "flight_search_results",
            "data": flights,
            "search_criteria": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "passenger_count": passenger_count,
                "class": flight_class
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_flight_by_id(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get specific flight by ID."""
        for flight in self.flights_data.get("data", []):
            if flight.get("id") == flight_id:
                return flight
        return None
    
    def get_available_routes(self) -> List[Dict[str, str]]:
        """Get all available flight routes."""
        routes = []
        for flight in self.flights_data.get("data", []):
            route = {
                "origin": flight.get("departureAirport"),
                "destination": flight.get("arrivalAirport"),
                "airline": flight.get("airline")
            }
            if route not in routes:
                routes.append(route)
        return routes


# Global instance
_flight_service = None

def get_flight_service() -> FlightService:
    """Get the global flight service instance."""
    global _flight_service
    if _flight_service is None:
        _flight_service = FlightService()
    return _flight_service