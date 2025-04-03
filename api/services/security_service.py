"""
Basic security services for the application
"""
import os
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


def setup_security_headers(app):
    """
    Configure security headers for the Flask application

    Args:
        app: Flask application instance
    """

    @app.after_request
    def add_security_headers(response):
        """Add security headers to responses"""
        # Content Security Policy
        response.headers[
            'Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'"

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Enable browser XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    return app


def generate_secure_filename(original_filename=None, file_type=None):
    """
    Generate a secure, random filename

    Args:
        original_filename: Original filename (optional)
        file_type: Type of file (e.g., 'audio', 'transcript') (optional)

    Returns:
        str: Secure filename with extension
    """
    # Generate a random UUID
    random_id = uuid.uuid4().hex

    # Get current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Add file type prefix if provided
    prefix = f"{file_type}_" if file_type else ""

    # Extract extension from original filename if provided
    extension = ""
    if original_filename:
        _, ext = os.path.splitext(original_filename)
        if ext:
            extension = ext.lower()

    # Combine to create secure filename
    secure_filename = f"{prefix}{timestamp}_{random_id}{extension}"

    return secure_filename


def log_data_access(user_id, resource_type, resource_id, action):
    """
    Log data access for audit purposes (stub implementation)

    Args:
        user_id: ID of the user accessing the data
        resource_type: Type of resource being accessed
        resource_id: ID of the resource
        action: Action being performed
    """
    # For now, just log the access
    logger.info(
        f"DATA ACCESS: User {user_id} performed {action} on {resource_type} {resource_id}"
    )


# Simplified audit log model function
def create_audit_log_model():
    """
    Create a simplified AuditLog model
    """
    from ..db import db

    class AuditLog(db.Model):
        """Model for tracking data access"""
        __tablename__ = 'audit_logs'

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        resource_type = db.Column(db.String(50), nullable=False)
        resource_id = db.Column(db.Integer, nullable=False)
        action = db.Column(db.String(50), nullable=False)
        timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        ip_address = db.Column(db.String(45), nullable=True)

        def __repr__(self):
            return f"<AuditLog {self.id}: {self.user_id} {self.action} {self.resource_type} {self.resource_id}>"

    return AuditLog