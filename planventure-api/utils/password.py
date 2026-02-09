import bcrypt


def generate_salt(rounds=12):
    """
    Generate a salt for password hashing.
    
    Args:
        rounds (int): The cost factor for bcrypt (default: 12)
        
    Returns:
        bytes: A salt value
    """
    return bcrypt.gensalt(rounds=rounds)


def hash_password(password, salt=None):
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): The plain text password to hash
        salt (bytes, optional): The salt to use. If None, generates a new salt
        
    Returns:
        str: The hashed password as a string
        
    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if salt is None:
        salt = generate_salt()
    
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def verify_password(password, password_hash):
    """
    Verify a password against a hash.
    
    Args:
        password (str): The plain text password to verify
        password_hash (str): The hashed password to check against
        
    Returns:
        bool: True if password matches, False otherwise
        
    Raises:
        ValueError: If password or hash is empty or None
    """
    if not password or not password_hash:
        raise ValueError("Password and hash cannot be empty")
    
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if isinstance(password_hash, str):
        password_hash = password_hash.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password, password_hash)
    except Exception:
        return False


def validate_password_strength(password, min_length=8):
    """
    Validate password strength.
    
    Args:
        password (str): The password to validate
        min_length (int): Minimum password length (default: 8)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digit characters"
    
    return True, None
