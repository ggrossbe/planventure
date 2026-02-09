from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta
from functools import wraps
from flask import jsonify


def generate_tokens(user_id, additional_claims=None):
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user_id (int): The user's ID
        additional_claims (dict, optional): Additional claims to include in the token
        
    Returns:
        dict: Dictionary containing access_token and refresh_token
    """
    identity = str(user_id)
    
    access_token = create_access_token(
        identity=identity,
        additional_claims=additional_claims or {}
    )
    
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=additional_claims or {}
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def generate_access_token(user_id, additional_claims=None, expires_delta=None):
    """
    Generate an access token for a user.
    
    Args:
        user_id (int): The user's ID
        additional_claims (dict, optional): Additional claims to include
        expires_delta (timedelta, optional): Custom expiration time
        
    Returns:
        str: The access token
    """
    identity = str(user_id)
    
    token = create_access_token(
        identity=identity,
        additional_claims=additional_claims or {},
        expires_delta=expires_delta
    )
    
    return token


def generate_refresh_token(user_id, additional_claims=None):
    """
    Generate a refresh token for a user.
    
    Args:
        user_id (int): The user's ID
        additional_claims (dict, optional): Additional claims to include
        
    Returns:
        str: The refresh token
    """
    identity = str(user_id)
    
    token = create_refresh_token(
        identity=identity,
        additional_claims=additional_claims or {}
    )
    
    return token


def get_current_user_id():
    """
    Get the current user's ID from the JWT token.
    
    Returns:
        int: The user's ID
    """
    identity = get_jwt_identity()
    return int(identity) if identity else None


def get_token_claims():
    """
    Get all claims from the current JWT token.
    
    Returns:
        dict: The JWT claims
    """
    return get_jwt()


def validate_token_user(user_id):
    """
    Validate that the current token belongs to the specified user.
    
    Args:
        user_id (int): The user ID to validate against
        
    Returns:
        bool: True if token matches user, False otherwise
    """
    current_user_id = get_current_user_id()
    return current_user_id == user_id


def token_required(fn):
    """
    Decorator to require a valid JWT token for a route.
    This is a wrapper around jwt_required for consistency.
    """
    from flask_jwt_extended import jwt_required
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    
    return wrapper


def token_optional(fn):
    """
    Decorator for routes where JWT token is optional.
    """
    from flask_jwt_extended import jwt_required
    
    @wraps(fn)
    @jwt_required(optional=True)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    
    return wrapper


def refresh_token_required(fn):
    """
    Decorator to require a valid refresh token for a route.
    """
    from flask_jwt_extended import jwt_required
    
    @wraps(fn)
    @jwt_required(refresh=True)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    
    return wrapper
