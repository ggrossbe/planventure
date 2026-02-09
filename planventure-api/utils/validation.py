import re


def is_valid_email(email):
    """
    Validate email format using regex.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return re.match(email_pattern, email.strip()) is not None


def validate_email(email):
    """
    Validate and normalize email address.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        tuple: (is_valid, normalized_email, error_message)
    """
    if not email:
        return False, None, "Email is required"
    
    email = email.strip().lower()
    
    if len(email) > 120:
        return False, None, "Email is too long (max 120 characters)"
    
    if not is_valid_email(email):
        return False, None, "Invalid email format"
    
    return True, email, None


def validate_registration_data(data):
    """
    Validate user registration data.
    
    Args:
        data (dict): Registration data containing email and password
        
    Returns:
        tuple: (is_valid, errors_dict)
    """
    errors = {}
    
    # Validate email
    email = data.get('email', '').strip()
    is_valid, normalized_email, error = validate_email(email)
    if not is_valid:
        errors['email'] = error
    
    # Validate password
    password = data.get('password', '')
    if not password:
        errors['password'] = "Password is required"
    elif len(password) < 8:
        errors['password'] = "Password must be at least 8 characters long"
    
    return len(errors) == 0, errors
