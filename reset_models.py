"""
Reset and initialize SQLAlchemy models
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def reset_sqlalchemy_models():
    """Reset all SQLAlchemy model mappings and recreate them"""
    logger.info("Resetting SQLAlchemy models...")

    # 1. Clear any existing mappers
    try:
        from sqlalchemy.orm import clear_mappers
        clear_mappers()
        logger.info("✓ Cleared existing mappers")
    except ImportError:
        logger.warning("Could not import clear_mappers")

    # 2. Create a Flask app and initialize db
    try:
        from flask import Flask
        from api.db import db

        # Get database URL directly
        db_url = os.environ.get('DATABASE_URL', '')

        # Handle sslmode for pg8000
        if 'sslmode=require' in db_url:
            db_url = db_url.replace('?sslmode=require', '')
            db_url = db_url.replace('&sslmode=require', '')

        # Convert postgres:// to postgresql+pg8000://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+pg8000://')
        elif db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+pg8000://')

        # Create app with direct database URL
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Add SSL connect_args for pg8000
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"ssl": True},
            "pool_pre_ping": True
        }

        # Initialize db
        db.init_app(app)

        logger.info(f"✓ Created Flask app with database URL: {db_url}")

        # 3. Initialize models within app context
        with app.app_context():
            # Import models - order matters here
            from api.models.user import User
            from api.models.transcript import Transcription
            from api.models.translation import Translation
            from api.models.audit_log import AuditLog

            # Create tables
            db.create_all()

            # Check if tables were created properly
            tables = db.engine.table_names()
            expected_tables = ['users', 'transcriptions', 'translations', 'audit_logs']

            missing_tables = [table for table in expected_tables if table not in tables]
            if missing_tables:
                logger.error(f"❌ Missing tables: {', '.join(missing_tables)}")
            else:
                logger.info(f"✓ All tables exist: {', '.join(tables)}")

            # Count rows in each table
            user_count = User.query.count()
            transcription_count = Transcription.query.count()
            translation_count = Translation.query.count()
            audit_log_count = AuditLog.query.count()

            logger.info(f"✓ Database table counts:")
            logger.info(f"  - Users: {user_count}")
            logger.info(f"  - Transcriptions: {transcription_count}")
            logger.info(f"  - Translations: {translation_count}")
            logger.info(f"  - Audit Logs: {audit_log_count}")

        logger.info("✓ SQLAlchemy models reset and initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error resetting SQLAlchemy models: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = reset_sqlalchemy_models()
    sys.exit(0 if success else 1)