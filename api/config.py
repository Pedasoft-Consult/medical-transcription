"""
Configuration loader for the Medical Transcription App
Loads settings from config.yaml and environment variables
"""
import os
import yaml
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """
    Configuration manager class for the application
    Loads settings from config.yaml and environment variables
    Environment variables take precedence over config file settings
    """

    def __init__(self, config_path: Optional[str] = None):
        # Default config path
        if config_path is None:
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(base_dir, 'config', 'config.yaml')

        # Load configuration from file
        self.config = self._load_config(config_path)

        # Get environment (development, testing, production)
        self.env = os.environ.get('FLASK_ENV', 'development')

        # Override with environment variables
        self._override_from_env()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to the config.yaml file

        Returns:
            Dict: Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return {}

    def _override_from_env(self):
        """Override configuration values from environment variables"""
        # Database URL
        if db_url := os.environ.get('DATABASE_URL'):
            if 'database' not in self.config:
                self.config['database'] = {}
            if self.env not in self.config['database']:
                self.config['database'][self.env] = {}
            self.config['database'][self.env]['url'] = db_url

        # JWT Secret Key
        if jwt_key := os.environ.get('SECRET_KEY'):
            if 'auth' not in self.config:
                self.config['auth'] = {}
            self.config['auth']['jwt_secret_key'] = jwt_key

        # Flask Secret Key
        if flask_key := os.environ.get('FLASK_SECRET_KEY'):
            if 'security' not in self.config:
                self.config['security'] = {}
            self.config['security']['secret_key'] = flask_key

        # Port
        if port := os.environ.get('PORT'):
            if 'environment' not in self.config:
                self.config['environment'] = {}
            if self.env not in self.config['environment']:
                self.config['environment'][self.env] = {}
            self.config['environment'][self.env]['port'] = int(port)

    def get_db_url(self) -> str:
        """Get the database URL for the current environment"""
        try:
            raw_url = self.config['database'][self.env]['url']

            # For PostgreSQL URLs, convert for SQLAlchemy
            if raw_url.startswith("postgres://"):
                # Remove SSL parameters that might cause issues
                main_url = raw_url.replace("postgres://", "postgresql://", 1)
                if "?" in main_url:
                    url_part, _ = main_url.split("?", 1)
                    return url_part
                return main_url
            return raw_url
        except (KeyError, TypeError):
            return "sqlite:///app.db"  # Default fallback
    def get_db_engine_options(self) -> Dict[str, Any]:
        """Get database engine options for the current environment"""
        try:
            return self.config['database'][self.env]['engine_options']
        except (KeyError, TypeError):
            return {"pool_recycle": 300, "pool_pre_ping": True}

    def get_jwt_secret_key(self) -> str:
        """Get the JWT secret key"""
        try:
            return self.config['auth']['jwt_secret_key']
        except (KeyError, TypeError):
            return "your-jwt-secret-key-change-this-in-production"

    def get_secret_key(self) -> str:
        """Get the Flask secret key"""
        try:
            return self.config['security']['secret_key']
        except (KeyError, TypeError):
            return "your-secret-key-change-this-in-production"

    def get_port(self) -> int:
        """Get the port for the current environment"""
        try:
            return self.config['environment'][self.env]['port']
        except (KeyError, TypeError):
            return 5000  # Default port

    def get_debug(self) -> bool:
        """Get debug mode for the current environment"""
        try:
            return self.config['environment'][self.env]['debug']
        except (KeyError, TypeError):
            return self.env == 'development'  # Default debug mode

    def get_static_folder(self) -> str:
        """Get the static folder path"""
        try:
            return self.config['app']['static_folder']
        except (KeyError, TypeError):
            return '../frontend/dist'

    def get_static_url_path(self) -> str:
        """Get the static URL path"""
        try:
            return self.config['app']['static_url_path']
        except (KeyError, TypeError):
            return ''

    def get_upload_directory(self) -> str:
        """Get the upload directory path"""
        try:
            return self.config['storage']['upload_directory']
        except (KeyError, TypeError):
            return 'uploads'

    def get_tts_output_directory(self) -> str:
        """Get the TTS output directory path"""
        try:
            return self.config['services']['tts']['output_directory']
        except (KeyError, TypeError):
            return 'tts_output'

    def get_allowed_audio_extensions(self) -> list:
        """Get the list of allowed audio file extensions"""
        try:
            return self.config['storage']['allowed_audio_extensions']
        except (KeyError, TypeError):
            return ['.wav', '.mp3', '.m4a', '.flac']

    def get_max_upload_size(self) -> int:
        """Get the maximum upload file size in bytes"""
        try:
            return self.config['storage']['max_upload_size']
        except (KeyError, TypeError):
            return 50000000  # 50MB default

    def get_speech_recognition_language(self) -> str:
        """Get the default speech recognition language"""
        try:
            return self.config['services']['speech_recognition']['default_language']
        except (KeyError, TypeError):
            return 'en-US'

    def get_default_translation_source(self) -> str:
        """Get the default translation source language"""
        try:
            return self.config['services']['translation']['default_source_language']
        except (KeyError, TypeError):
            return 'en'

    def get_default_translation_target(self) -> str:
        """Get the default translation target language"""
        try:
            return self.config['services']['translation']['default_target_language']
        except (KeyError, TypeError):
            return 'es'

    def get_logging_config(self) -> Dict[str, Any]:
        """Get the logging configuration"""
        try:
            return self.config['logging']
        except (KeyError, TypeError):
            return {
                'level': 'INFO',
                'format': '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
                'file': 'logs/app.log',
                'max_size': 10240,
                'backup_count': 10
            }

    def get_swagger_config(self) -> Dict[str, Any]:
        """Get the Swagger documentation configuration"""
        try:
            return self.config['swagger']
        except (KeyError, TypeError):
            return {
                'title': 'Medical Transcription API',
                'version': '1.0.0',
                'description': 'API for medical audio transcription and translation',
                'openapi_version': '3.0.2',
                'contact_email': 'contact@example.com'
            }

    def get_api_base_url(self) -> str:
        """Get the API base URL"""
        try:
            return self.config['api']['base_url']
        except (KeyError, TypeError):
            return '/api'

    def get_jwt_algorithm(self) -> str:
        """Get the JWT algorithm"""
        try:
            return self.config['auth']['algorithm']
        except (KeyError, TypeError):
            return 'HS256'

    def get_jwt_expire_minutes(self) -> int:
        """Get the JWT expiration time in minutes"""
        try:
            return self.config['auth']['access_token_expire_minutes']
        except (KeyError, TypeError):
            return 30


# Create a global config instance
config = Config()