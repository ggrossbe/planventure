from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import User
from extensions import db


def require_auth(fn):
    """
    Middleware to require valid JWT authentication.
    
    Usage:
        @require_auth
        def protected_route():
            return jsonify({'message': 'Success'})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': 'authentication_required',
                'message': 'Valid authentication token is required'
            }), 401
    
    return wrapper


def require_user(fn):
    """
    Middleware to require authentication and inject current user.
    Adds 'current_user' to kwargs.
    
    Usage:
        @require_user
        def protected_route(current_user):
            return jsonify({'user': current_user.to_dict()})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'error': 'user_not_found',
                    'message': 'User account not found'
                }), 404
            
            kwargs['current_user'] = user
            return fn(*args, **kwargs)
            
        except ValueError:
            return jsonify({
                'error': 'invalid_token',
                'message': 'Invalid token format'
            }), 401
        except Exception as e:
            return jsonify({
                'error': 'authentication_failed',
                'message': 'Authentication failed'
            }), 401
    
    return wrapper


def require_user_ownership(model_class, id_param='id', foreign_key='user_id'):
    """
    Middleware to verify the authenticated user owns the requested resource.
    
    Args:
        model_class: The SQLAlchemy model class to check
        id_param: The URL parameter name for the resource ID
        foreign_key: The foreign key field name linking to user
    
    Usage:
        @require_user_ownership(Trip, id_param='trip_id')
        def update_trip(trip_id, current_user, resource):
            return jsonify({'trip': resource.to_dict()})
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = int(get_jwt_identity())
                
                user = User.query.get(user_id)
                if not user:
                    return jsonify({
                        'error': 'user_not_found',
                        'message': 'User account not found'
                    }), 404
                
                # Get resource ID from kwargs or view_args
                resource_id = kwargs.get(id_param)
                if resource_id is None:
                    return jsonify({
                        'error': 'invalid_request',
                        'message': f'Missing {id_param} parameter'
                    }), 400
                
                # Query the resource
                resource = model_class.query.get(resource_id)
                if not resource:
                    return jsonify({
                        'error': 'resource_not_found',
                        'message': f'{model_class.__name__} not found'
                    }), 404
                
                # Check ownership
                if getattr(resource, foreign_key) != user_id:
                    return jsonify({
                        'error': 'forbidden',
                        'message': 'You do not have permission to access this resource'
                    }), 403
                
                # Inject user and resource into kwargs
                kwargs['current_user'] = user
                kwargs['resource'] = resource
                
                return fn(*args, **kwargs)
                
            except ValueError:
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Invalid token format'
                }), 401
            except Exception as e:
                return jsonify({
                    'error': 'authorization_failed',
                    'message': 'Authorization failed'
                }), 500
        
        return wrapper
    return decorator


def optional_auth(fn):
    """
    Middleware for optional authentication.
    Injects current_user if authenticated, None otherwise.
    
    Usage:
        @optional_auth
        def public_route(current_user=None):
            if current_user:
                return jsonify({'message': 'Authenticated'})
            return jsonify({'message': 'Public access'})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if user_id:
                user = User.query.get(int(user_id))
                kwargs['current_user'] = user
            else:
                kwargs['current_user'] = None
                
        except Exception:
            kwargs['current_user'] = None
        
        return fn(*args, **kwargs)
    
    return wrapper


def check_token_freshness(fn):
    """
    Middleware to require a fresh token (recently logged in).
    Useful for sensitive operations like password changes.
    
    Usage:
        @check_token_freshness
        def change_password():
            return jsonify({'message': 'Password changed'})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(fresh=True)
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': 'fresh_token_required',
                'message': 'A fresh authentication token is required for this action'
            }), 401
    
    return wrapper


def rate_limit_by_user(max_requests=100, window_seconds=3600):
    """
    Simple rate limiting middleware per user.
    Note: For production, use Redis or similar for distributed rate limiting.
    
    Args:
        max_requests: Maximum number of requests
        window_seconds: Time window in seconds
    """
    from datetime import datetime, timedelta
    
    request_counts = {}
    
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                now = datetime.utcnow()
                key = f"{user_id}"
                
                # Clean old entries
                if key in request_counts:
                    request_counts[key] = [
                        req_time for req_time in request_counts[key]
                        if now - req_time < timedelta(seconds=window_seconds)
                    ]
                else:
                    request_counts[key] = []
                
                # Check rate limit
                if len(request_counts[key]) >= max_requests:
                    return jsonify({
                        'error': 'rate_limit_exceeded',
                        'message': f'Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds'
                    }), 429
                
                # Add current request
                request_counts[key].append(now)
                
                return fn(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'error': 'authentication_required',
                    'message': 'Valid authentication required for rate limiting'
                }), 401
        
        return wrapper
    return decorator