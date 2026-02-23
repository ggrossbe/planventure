from flask import Blueprint, request, jsonify
from extensions import db
from models import Trip
from middleware import jwt_required_with_user, user_owns_resource
from datetime import datetime
from sqlalchemy import and_, or_

trips_bp = Blueprint('trips', __name__, url_prefix='/api/trips')


def validate_trip_data(data, required_fields=None):
    """
    Validate trip data.
    
    Args:
        data (dict): Trip data to validate
        required_fields (list): List of required field names
        
    Returns:
        tuple: (is_valid, errors_dict)
    """
    errors = {}
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            errors['missing_fields'] = f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate destination
    if 'destination' in data:
        if not data['destination'] or len(data['destination'].strip()) == 0:
            errors['destination'] = "Destination cannot be empty"
        elif len(data['destination']) > 255:
            errors['destination'] = "Destination is too long (max 255 characters)"
    
    # Validate dates
    if 'start_date' in data and 'end_date' in data:
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            if end_date < start_date:
                errors['dates'] = "End date must be after or equal to start date"
            
            if start_date < datetime.now().date():
                errors['start_date'] = "Start date cannot be in the past"
                
        except ValueError:
            errors['dates'] = "Invalid date format. Use YYYY-MM-DD"
    
    # Validate coordinates
    if 'latitude' in data and data['latitude'] is not None:
        try:
            lat = float(data['latitude'])
            if lat < -90 or lat > 90:
                errors['latitude'] = "Latitude must be between -90 and 90"
        except (ValueError, TypeError):
            errors['latitude'] = "Invalid latitude value"
    
    if 'longitude' in data and data['longitude'] is not None:
        try:
            lon = float(data['longitude'])
            if lon < -180 or lon > 180:
                errors['longitude'] = "Longitude must be between -180 and 180"
        except (ValueError, TypeError):
            errors['longitude'] = "Invalid longitude value"
    
    return len(errors) == 0, errors


@trips_bp.route('', methods=['POST'])
@jwt_required_with_user
def create_trip(user=None):
    """
    Create a new trip for the authenticated user.
    
    Expected JSON payload:
    {
        "destination": "Paris, France",
        "start_date": "2026-06-01",
        "end_date": "2026-06-07",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "itinerary": "Day 1: Eiffel Tower..."
    }
    
    Returns:
        201: Trip created successfully
        400: Invalid input data
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        required_fields = ['destination', 'start_date', 'end_date']
        is_valid, errors = validate_trip_data(data, required_fields)
        
        if not is_valid:
            return jsonify({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'errors': errors
            }), 400
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Create trip
        trip = Trip(
            user_id=user.id,
            destination=data['destination'].strip(),
            start_date=start_date,
            end_date=end_date,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            itinerary=data.get('itinerary', '').strip() if data.get('itinerary') else None
        )
        
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'message': 'Trip created successfully',
            'trip': trip.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while creating the trip'
        }), 500


@trips_bp.route('', methods=['GET'])
@jwt_required_with_user
def get_user_trips(user=None):
    """
    Get all trips for the authenticated user with optional filtering.
    
    Query parameters:
        - sort: Sort order (newest, oldest, alphabetical)
        - status: Filter by status (upcoming, past, current)
        - search: Search in destination
        - limit: Number of results (default: 50)
        - offset: Pagination offset (default: 0)
    
    Returns:
        200: List of trips
        500: Server error
    """
    try:
        # Get query parameters
        sort_order = request.args.get('sort', 'newest')
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Trip.query.filter_by(user_id=user.id)
        
        # Apply search filter
        if search_query:
            query = query.filter(Trip.destination.ilike(f'%{search_query}%'))
        
        # Apply status filter
        today = datetime.now().date()
        if status_filter == 'upcoming':
            query = query.filter(Trip.start_date > today)
        elif status_filter == 'past':
            query = query.filter(Trip.end_date < today)
        elif status_filter == 'current':
            query = query.filter(and_(Trip.start_date <= today, Trip.end_date >= today))
        
        # Apply sorting
        if sort_order == 'oldest':
            query = query.order_by(Trip.start_date.asc())
        elif sort_order == 'alphabetical':
            query = query.order_by(Trip.destination.asc())
        else:  # newest
            query = query.order_by(Trip.start_date.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        trips = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'trips': [trip.to_dict() for trip in trips],
            'count': len(trips),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'invalid_parameters',
            'message': 'Invalid query parameters'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while fetching trips'
        }), 500


@trips_bp.route('/<int:trip_id>', methods=['GET'])
@jwt_required_with_user
def get_trip(trip_id, user=None):
    """
    Get a specific trip by ID.
    
    Returns:
        200: Trip details
        403: User doesn't own the trip
        404: Trip not found
        500: Server error
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'error': 'not_found',
                'message': 'Trip not found'
            }), 404
        
        # Verify user owns the trip
        if trip.user_id != user.id:
            return jsonify({
                'error': 'forbidden',
                'message': 'You do not have permission to view this trip'
            }), 403
        
        return jsonify({
            'trip': trip.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while fetching the trip'
        }), 500


@trips_bp.route('/<int:trip_id>', methods=['PUT'])
@jwt_required_with_user
def update_trip(trip_id, user=None):
    """
    Update a trip. User must own the trip.
    
    Expected JSON payload (all fields optional):
    {
        "destination": "Rome, Italy",
        "start_date": "2026-07-01",
        "end_date": "2026-07-10",
        "latitude": 41.9028,
        "longitude": 12.4964,
        "itinerary": "Updated itinerary..."
    }
    
    Returns:
        200: Trip updated successfully
        400: Invalid input data
        403: User doesn't own the trip
        404: Trip not found
        500: Server error
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'error': 'not_found',
                'message': 'Trip not found'
            }), 404
        
        # Verify user owns the trip
        if trip.user_id != user.id:
            return jsonify({
                'error': 'forbidden',
                'message': 'You do not have permission to update this trip'
            }), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate data (no required fields for update)
        is_valid, errors = validate_trip_data(data)
        
        if not is_valid:
            return jsonify({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'errors': errors
            }), 400
        
        # Update fields
        if 'destination' in data:
            trip.destination = data['destination'].strip()
        
        if 'start_date' in data:
            trip.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        if 'end_date' in data:
            trip.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if 'latitude' in data:
            trip.latitude = data['latitude']
        
        if 'longitude' in data:
            trip.longitude = data['longitude']
        
        if 'itinerary' in data:
            trip.itinerary = data['itinerary'].strip() if data['itinerary'] else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Trip updated successfully',
            'trip': trip.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'validation_error',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while updating the trip'
        }), 500


@trips_bp.route('/<int:trip_id>', methods=['PATCH'])
@jwt_required_with_user
def partial_update_trip(trip_id, user=None):
    """
    Partially update a trip (same as PUT but semantically more correct for partial updates).
    """
    return update_trip(trip_id, user=user)


@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
@jwt_required_with_user
def delete_trip(trip_id, user=None):
    """
    Delete a trip. User must own the trip.
    
    Returns:
        200: Trip deleted successfully
        403: User doesn't own the trip
        404: Trip not found
        500: Server error
    """
    try:
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'error': 'not_found',
                'message': 'Trip not found'
            }), 404
        
        # Verify user owns the trip
        if trip.user_id != user.id:
            return jsonify({
                'error': 'forbidden',
                'message': 'You do not have permission to delete this trip'
            }), 403
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({
            'message': 'Trip deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while deleting the trip'
        }), 500


@trips_bp.route('/stats', methods=['GET'])
@jwt_required_with_user
def get_trip_stats(user=None):
    """
    Get statistics about the user's trips.
    
    Returns:
        200: Trip statistics
        500: Server error
    """
    try:
        today = datetime.now().date()
        
        all_trips = Trip.query.filter_by(user_id=user.id).all()
        
        upcoming_trips = [t for t in all_trips if t.start_date > today]
        past_trips = [t for t in all_trips if t.end_date < today]
        current_trips = [t for t in all_trips if t.start_date <= today <= t.end_date]
        
        total_days = sum(t.duration_days for t in all_trips)
        
        stats = {
            'total_trips': len(all_trips),
            'upcoming_trips': len(upcoming_trips),
            'past_trips': len(past_trips),
            'current_trips': len(current_trips),
            'total_travel_days': total_days,
            'destinations_visited': len(set(t.destination for t in past_trips))
        }
        
        return jsonify({
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'server_error',
            'message': 'An error occurred while calculating statistics'
        }), 500