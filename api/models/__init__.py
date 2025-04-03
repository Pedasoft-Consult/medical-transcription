"""
1. Fix the models/__init__.py file to properly organize imports
   and avoid duplicate model registrations
"""

# api/models/__init__.py
"""
Models package for SQLAlchemy models
"""
# Import models here to ensure they're registered with SQLAlchemy only once
from .user import User
from .transcript import Transcription
from .translation import Translation

# Leave a clean namespace for imports from this package
__all__ = ['User', 'Transcription', 'Translation']