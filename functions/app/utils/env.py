"""Environment configuration utility for Firebase Functions."""

import os


def get_env_var(key: str, default: str = None) -> str:
    """
    Get environment variable with support for both local and Firebase Functions.
    
    In local development: Uses os.getenv() to read from .env file
    In Firebase Functions: Uses os.getenv() which reads from functions config/secrets
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def is_local_development() -> bool:
    """Check if running in local development environment."""
    return os.getenv('FUNCTIONS_EMULATOR') == 'true'


def is_production() -> bool:
    """Check if running in Firebase Functions production environment."""
    return not is_local_development()


def get_firebase_config():
    """Get Firebase configuration for current environment."""
    return {
        'service_account_path': get_env_var('SERVICE_ACCOUNT_PATH'),
        'web_api_key': get_env_var('WEB_API_KEY'),
        'use_emulator': is_local_development()
    }


def get_google_config():
    """Get Google API configuration."""
    return {
        'api_key': get_env_var('GOOGLE_API_KEY'),
        'places_api_key': get_env_var('GOOGLE_PLACES_API_KEY'),
        'genai_use_vertexai': get_env_var('GOOGLE_GENAI_USE_VERTEXAI', '0') == '1'
    }