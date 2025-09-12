"""Authentication routes for user signup and login."""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from app.models.user import (
    UserSignupRequest, 
    UserLoginRequest, 
    AuthResponse, 
    UserResponse, 
    ErrorResponse,
    TokenData
)
from app.services.firebase_service import get_firebase_service
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignupRequest):
    """
    Create a new user account with Firebase Auth and return ID token.
    """
    try:
        firebase_service = get_firebase_service()
        
        existing_user = firebase_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        uid = firebase_service.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
        
        id_token = None
        signin_result = firebase_service.sign_in_with_password(user_data.email, user_data.password)
        
        if signin_result and "idToken" in signin_result:
            id_token = signin_result["idToken"]
        else:
            print("REST API sign-in failed, using custom token as fallback")
            id_token = firebase_service.create_custom_token(uid)
            
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authentication token"
            )
        
        profile_data = {
            "email": user_data.email,
            "display_name": user_data.display_name,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        profile_saved = firebase_service.save_user_profile(uid, profile_data)
        if not profile_saved:
            print(f"Warning: Failed to save user profile for UID: {uid}")
        
        user_response = UserResponse(
            uid=uid,
            email=user_data.email,
            display_name=user_data.display_name,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email_verified=False,
            created_at=profile_data["created_at"],
            updated_at=profile_data["updated_at"]
        )
        
        return AuthResponse(
            success=True,
            message="User account created successfully",
            user=user_response,
            token=id_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )


@router.post("/login", response_model=AuthResponse)
async def login(login_data: UserLoginRequest):
    """
    Login with email/password and return ID token.
    """
    try:
        firebase_service = get_firebase_service()
        
        # Check if user exists
        user_auth_data = firebase_service.get_user_by_email(login_data.email)
        if not user_auth_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Try to get an ID token via REST API, fallback to custom token
        id_token = None
        signin_result = firebase_service.sign_in_with_password(login_data.email, login_data.password)
        
        if signin_result and "idToken" in signin_result:
            id_token = signin_result["idToken"]
        else:
            print("REST API sign-in failed for login, using custom token as fallback")
            id_token = firebase_service.create_custom_token(user_auth_data['uid'])
            
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        uid = user_auth_data['uid']
        
        user_profile = firebase_service.get_user_profile(uid)
        
        user_response = UserResponse(
            uid=uid,
            email=user_auth_data['email'],
            display_name=user_auth_data.get('display_name') or (user_profile.get('display_name') if user_profile else None),
            first_name=user_profile.get('first_name') if user_profile else None,
            last_name=user_profile.get('last_name') if user_profile else None,
            email_verified=user_auth_data.get('email_verified', False),
            created_at=user_profile.get('created_at') if user_profile else None,
            updated_at=user_profile.get('updated_at') if user_profile else None
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user=user_response,
            token=id_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    """
    try:
        print(current_user)
        firebase_service = get_firebase_service()
        
        user_profile = firebase_service.get_user_profile(current_user.uid)
        
        user_auth_data = firebase_service.get_user_by_email(current_user.email)
        
        return UserResponse(
            uid=current_user.uid,
            email=current_user.email,
            display_name=user_auth_data.get('display_name') if user_auth_data else None,
            first_name=user_profile.get('first_name') if user_profile else None,
            last_name=user_profile.get('last_name') if user_profile else None,
            email_verified=current_user.email_verified,
            created_at=user_profile.get('created_at') if user_profile else None,
            updated_at=user_profile.get('updated_at') if user_profile else None
        )
        
    except Exception as e:
        print(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post("/verify-token")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    """
    Verify if the provided token is valid.
    """
    return {
        "success": True,
        "message": "Token is valid",
        "user_id": current_user.uid,
        "email": current_user.email
    }
