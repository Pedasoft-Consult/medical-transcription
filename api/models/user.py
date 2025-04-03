"""
Enhanced User model with improved security features and singleton pattern
"""
import re
import logging
from datetime import datetime
import bcrypt
from flask import current_app
from ..db import db
from . import ModelRegistry

logger = logging.getLogger(__name__)

# Use the ModelRegistry to ensure model is only defined once
@ModelRegistry.register('User')
class User(db.Model):
    """Model for user accounts with enhanced security"""
    __tablename__ = 'users'

    # Important: Add extend_existing=True to avoid table redefinition errors
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Add fields for password reset and account security
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"

    def set_password(self, password):
        """Hash and set the password with enhanced validation"""
        # Validate password complexity
        is_valid, message = self.validate_password(password)
        if not is_valid:
            raise ValueError(message)

        password_bytes = password.encode('utf-8')
        # Use a higher cost factor for stronger hashing
        salt = bcrypt.gensalt(rounds=12)
        self.hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Update password change timestamp
        self.password_changed_at = datetime.utcnow()

        # Reset any password reset token
        self.password_reset_token = None
        self.password_reset_expires = None

        logger.info(f"Password set for user {self.id}")

    def check_password(self, password):
        """Check if the provided password matches the stored hashed password"""
        if not password or not self.hashed_password:
            return False

        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = self.hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Password check error for user {self.id}: {str(e)}")
            return False

    @staticmethod
    def validate_password(password):
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            tuple: (is_valid, message)
        """
        if not password:
            return False, "Password cannot be empty"

        if len(password) < 12:
            return False, "Password must be at least 12 characters long"

        # Check for complexity requirements
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[^A-Za-z0-9]', password))

        missing = []
        if not has_upper:
            missing.append("uppercase letter")
        if not has_lower:
            missing.append("lowercase letter")
        if not has_digit:
            missing.append("digit")
        if not has_special:
            missing.append("special character")

        if missing:
            return False, f"Password must contain at least one {', '.join(missing)}"

        # Check for common passwords (simplified)
        common_passwords = [
            "password123", "qwerty123", "123456789", "admin123", "welcome1",
            "letmein123", "123qwerty", "adminadmin", "P@ssword1", "Password123"
        ]

        if password.lower() in common_passwords:
            return False, "Password is too common and easily guessable"

        return True, "Password meets requirements"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None
        }

    def record_login(self):
        """Record successful login"""
        self.last_login_at = datetime.utcnow()
        self.login_attempts = 0
        db.session.commit()