"""
6. Update the security.py file to avoid circular imports
"""

# api/security.py
"""
Security utilities for JWT authentication
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from .config import config

# JWT Configuration
SECRET_KEY = config.get_jwt_secret_key()
ALGORITHM = config.get_jwt_algorithm()
ACCESS_TOKEN_EXPIRE_MINUTES = config.get_jwt_expire_minutes()


def get_token_from_header():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None


def token_required(f):
    """Decorator to validate JWT tokens for protected routes"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Import User model here to avoid circular imports
            from .models import User
            user = User.query.filter_by(username=payload['sub']).first()
            if not user:
                return jsonify({'message': 'Invalid token'}), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated


def create_access_token(data, expires_delta=None):
    """Create a new JWT token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt