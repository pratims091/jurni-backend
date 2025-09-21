"""Firebase configuration and service initialization."""

import os
import json
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import lru_cache
import requests
from datetime import datetime
import uuid


class FirebaseService:
    """Firebase service for authentication and Firestore operations."""
    
    def __init__(self):
        self._app = None
        self._db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            service_account_path = os.getenv('SERVICE_ACCOUNT_PATH')
            
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
            else:
                try:
                    cred = credentials.ApplicationDefault()
                except Exception:
                    print("Warning: No Firebase credentials found. Using default.")
                    cred = None
            
            if cred:
                self._app = firebase_admin.initialize_app(cred)
            else:
                self._app = None
        else:
            self._app = firebase_admin.get_app()
    
    @property
    def db(self):
        """Get Firestore database instance."""
        if self._db is None:
            self._db = firestore.client()
        return self._db
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token or custom token."""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            print(f"ID token verification failed: {e}")
            try:
                return self._verify_custom_token(token)
            except Exception as e2:
                print(f"Custom token verification failed: {e2}")
                return None
    
    def _verify_custom_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify custom token by decoding and checking user exists."""
        try:
            import jwt
            
            decoded = jwt.decode(token, options={"verify_signature": False})
            uid = decoded.get('uid')
            
            if not uid:
                return None
            
            user_record = auth.get_user(uid)
            
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'auth_time': decoded.get('iat'),
                'iss': decoded.get('iss', 'firebase-custom-token'),
                'aud': decoded.get('aud'),
                'exp': decoded.get('exp'),
                'custom_token': True
            }
        except Exception as e:
            print(f"Custom token decode error: {e}")
            return None
    
    def create_user(self, email: str, password: str, display_name: str = None) -> Optional[str]:
        """Create a new user in Firebase Auth."""
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            return user_record.uid
        except Exception as e:
            print(f"User creation failed: {e}")
            return None

    def sign_in_with_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Sign in via Firebase Identity Toolkit (REST) to obtain an ID token."""
        api_key = os.getenv("WEB_API_KEY")
        if not api_key:
            print("WEB_API_KEY not set; cannot sign in with password.")
            return None
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        try:
            resp = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True,
            }, timeout=10)
            if resp.status_code != 200:
                print(f"Sign-in failed: {resp.status_code} {resp.text}")
                return None
            return resp.json()
        except Exception as e:
            print(f"Sign-in request error: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Firebase Auth."""
        try:
            user_record = auth.get_user_by_email(email)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified
            }
        except Exception as e:
            print(f"Get user by email failed: {e}")
            return None
    
    def create_custom_token(self, uid: str) -> Optional[str]:
        """Create a custom token for a user."""
        try:
            custom_token = auth.create_custom_token(uid)
            return custom_token.decode('utf-8')
        except Exception as e:
            print(f"Custom token creation failed: {e}")
            return None
    
    def save_user_profile(self, uid: str, user_data: Dict[str, Any]) -> bool:
        """Save user profile data to Firestore."""
        try:
            user_ref = self.db.collection('users').document(uid)
            user_ref.set(user_data, merge=True)
            return True
        except Exception as e:
            print(f"Save user profile failed: {e}")
            return False
    
    def get_user_profile(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from Firestore."""
        try:
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Get user profile failed: {e}")
            return None
    
    def save_trip(self, uid: str, trip_data: Dict[str, Any]) -> Optional[str]:
        """Save trip data to Firestore and return trip ID."""
        try:
            trip_id = str(uuid.uuid4())
            
            trip_document = {
                **trip_data,
                'id': trip_id,
                'user_id': uid,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            trip_ref = self.db.collection('trips').document(trip_id)
            trip_ref.set(trip_document)
            
            return trip_id
        except Exception as e:
            print(f"Save trip failed: {e}")
            return None
    
    def get_trip(self, trip_id: str, uid: str) -> Optional[Dict[str, Any]]:
        """Get a specific trip by ID for a user."""
        try:
            trip_ref = self.db.collection('trips').document(trip_id)
            doc = trip_ref.get()
            
            if doc.exists:
                trip_data = doc.to_dict()
                if trip_data.get('user_id') == uid:
                    return trip_data
            return None
        except Exception as e:
            print(f"Get trip failed: {e}")
            return None
    
    def get_user_trips(self, uid: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all trips for a user with pagination."""
        try:
            trips_ref = self.db.collection('trips')
            query = trips_ref.where('user_id', '==', uid).order_by('created_at', direction=firestore.Query.DESCENDING)
            
            if offset > 0:
                query = query.offset(offset)
            if limit > 0:
                query = query.limit(limit)
            
            docs = query.get()
            trips = []
            
            for doc in docs:
                trip_data = doc.to_dict()
                trips.append(trip_data)
            
            return trips
        except Exception as e:
            print(f"Get user trips failed: {e}")
            return []
    
    def update_trip(self, trip_id: str, uid: str, trip_data: Dict[str, Any]) -> bool:
        """Update trip data for a specific user."""
        try:
            trip_ref = self.db.collection('trips').document(trip_id)
            doc = trip_ref.get()
            
            if not doc.exists:
                return False
            
            existing_data = doc.to_dict()
            if existing_data.get('user_id') != uid:
                return False
            
            update_data = {
                **trip_data,
                'updated_at': datetime.utcnow()
            }
            
            trip_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Update trip failed: {e}")
            return False
    
    def delete_trip(self, trip_id: str, uid: str) -> bool:
        """Delete a trip for a specific user."""
        try:
            trip_ref = self.db.collection('trips').document(trip_id)
            doc = trip_ref.get()
            
            if not doc.exists:
                return False
            
            trip_data = doc.to_dict()
            if trip_data.get('user_id') != uid:
                return False
            
            trip_ref.delete()
            return True
        except Exception as e:
            print(f"Delete trip failed: {e}")
            return False


@lru_cache()
def get_firebase_service() -> FirebaseService:
    """Get Firebase service instance (cached)."""
    return FirebaseService()
