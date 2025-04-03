"""
Routes package initialization
"""
# Import blueprints to make them available for registration
from .auth import auth_bp
from .ai_translation import ai_translation_bp
from .ai_transcription import ai_transcription_bp