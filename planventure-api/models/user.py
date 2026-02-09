from datetime import datetime
from extensions import db
from utils.password import hash_password, verify_password, validate_password_strength


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Trip
    trips = db.relationship('Trip', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password, validate=True):
        """
        Hash and set the user's password.

        Args:
            password (str): The plain text password
            validate (bool): Whether to validate password strength (default: True)

        Raises:
            ValueError: If password validation fails
        """
        if validate:
            is_valid, error_message = validate_password_strength(password)
            if not is_valid:
                raise ValueError(error_message)

        self.password_hash = hash_password(password)

    def check_password(self, password):
        """
        Check if the provided password matches the hash.

        Args:
            password (str): The plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return verify_password(password, self.password_hash)

    def to_dict(self):
        """Convert user object to dictionary (excluding password_hash)."""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
