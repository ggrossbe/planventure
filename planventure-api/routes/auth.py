from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from utils.validation import validate_registration_data, validate_email
from utils.jwt_utils import generate_tokens
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
import datetime
from functools import wraps
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user with email and password.
    
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePassword123"
    }
    
    Returns:
        201: User created successfully with tokens
        400: Invalid input data
        409: Email already exists
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate input data
        is_valid, errors = validate_registration_data(data)
        if not is_valid:
            return jsonify({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'errors': errors
            }), 400
        
        # Normalize email
        _, email, _ = validate_email(data['email'])
        password = data['password']
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'error': 'email_exists',
                'message': 'An account with this email already exists'
            }), 409
        
        # Create new user
        user = User(email=email)
        
        try:
            user.set_password(password)
        except ValueError as e:
            return jsonify({
                'error': 'password_validation_error',
                'message': str(e)
            }), 400
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        tokens = generate_tokens(user.id, additional_claims={'email': user.email})
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'tokens': tokens
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error': 'email_exists',
            'message': 'An account with this email already exists'
        }), 409
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred during registration'
        }), 500


@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """
    Check if an email is available for registration.
    
    Expected JSON payload:
    {
        "email": "user@example.com"
    }
    
    Returns:
        200: Email availability status
        400: Invalid email format
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Email is required'
            }), 400
        
        # Validate email format
        is_valid, email, error = validate_email(data['email'])
        if not is_valid:
            return jsonify({
                'error': 'validation_error',
                'message': error,
                'available': False
            }), 400
        
        # Check database
        existing_user = User.query.filter_by(email=email).first()
        
        return jsonify({
            'email': email,
            'available': existing_user is None
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while checking email'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login route that generates JWT token"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Generate JWT token
    token = create_access_token(identity=str(user.id), expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
    
    return jsonify({
        'token': token,
        'message': 'Login successful'
    }), 200


# Decorator to protect routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if user still exists in database
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({"error": "User not found"}), 401
                
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
    return decorated


# Example protected route
@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected_route():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if not user:
        return jsonify({"error": "User not found"}), 401
    return jsonify(logged_in_as=user.email), 200