"""Firebase-based session management for travel planner."""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from app.services.firebase_service import get_firebase_service


class FirebaseSessionManager:
    """Manages travel planner sessions in Firebase Firestore."""
    
    def __init__(self):
        self.firebase_service = get_firebase_service()
        self.collection_name = "travel_planner_sessions"
    
    def create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session in Firebase."""
        if not session_id:
            session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "active",
            "conversation_history": [],
            "session_state": {},
            "metadata": {
                "app_name": "travel_planner_agent",
                "version": "1.0"
            }
        }
        
        # Store in Firebase
        doc_ref = self.firebase_service.db.collection(self.collection_name).document(session_id)
        doc_ref.set(session_data)
        
        return {
            "id": session_id,
            "appName": "travel_planner_agent",
            "userId": user_id,
            "state": {},
            "events": [],
            "lastUpdateTime": datetime.now().timestamp()
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Firebase."""
        try:
            doc_ref = self.firebase_service.db.collection(self.collection_name).document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return {
                    "id": session_id,
                    "appName": "travel_planner_agent",
                    "userId": data.get("user_id"),
                    "state": data.get("session_state", {}),
                    "events": data.get("conversation_history", []),
                    "lastUpdateTime": datetime.now().timestamp()
                }
            return None
        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, events: list, state: Dict[str, Any]) -> bool:
        """Update session with new events and state."""
        try:
            doc_ref = self.firebase_service.db.collection(self.collection_name).document(session_id)
            doc_ref.update({
                "conversation_history": events,
                "session_state": state,
                "last_updated": datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error updating session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Firebase."""
        try:
            doc_ref = self.firebase_service.db.collection(self.collection_name).document(session_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False


# Global instance
_firebase_session_manager = None


def get_firebase_session_manager() -> FirebaseSessionManager:
    """Get the global Firebase session manager instance."""
    global _firebase_session_manager
    if _firebase_session_manager is None:
        _firebase_session_manager = FirebaseSessionManager()
    return _firebase_session_manager
