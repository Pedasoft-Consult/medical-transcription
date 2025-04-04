"""
Reset and initialize SQLAlchemy models
"""
import os
import sys
import logging
import ssl
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

        # Create SSL context for database connection
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Add SSL connect_args for pg8000
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"ssl_context": ssl_context},
            "pool_pre_ping": True
        }

        # Initialize db
        db.init_app(app)

        logger.info(f"✓ Created Flask app with database URL: {db_url}")

        # 3. Initialize models within app context
        with app.app_context():
            # Import models - order matters here
            try:
                from api.models.user import User
                logger.info("✓ User model imported")
            except Exception as e:
                logger.error(f"❌ Failed to import User model: {str(e)}")

            try:
                from api.models.transcript import Transcription
                logger.info("✓ Transcription model imported")
            except Exception as e:
                logger.error(f"❌ Failed to import Transcription model: {str(e)}")

            try:
                from api.models.translation import Translation
                logger.info("✓ Translation model imported")
            except Exception as e:
                logger.error(f"❌ Failed to import Translation model: {str(e)}")

            try:
                from api.models.audit_log import AuditLog
                logger.info("✓ AuditLog model imported")
            except Exception as e:
                logger.error(f"❌ Failed to import AuditLog model: {str(e)}")

            # Create tables
            try:
                db.create_all()
                logger.info("✓ Tables created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create tables: {str(e)}")
                # Try to provide more specific error info
                try:
                    from sqlalchemy import text
                    db.session.execute(text("SELECT 1"))
                    logger.info("  - Basic database connection is working")
                except Exception as db_e:
                    logger.error(f"  - Database connection test failed: {str(db_e)}")

            # Check if tables were created properly
            try:
                tables = db.engine.table_names()
                expected_tables = ['users', 'transcriptions', 'translations', 'audit_logs']

                missing_tables = [table for table in expected_tables if table not in tables]
                if missing_tables:
                    logger.error(f"❌ Missing tables: {', '.join(missing_tables)}")
                else:
                    logger.info(f"✓ All expected tables exist: {', '.join(tables)}")

                # Try to count rows in each table
                from api.models.user import User
                from api.models.transcript import Transcription
                from api.models.translation import Translation
                from api.models.audit_log import AuditLog

                user_count = User.query.count()
                transcription_count = Transcription.query.count()
                translation_count = Translation.query.count()
                audit_log_count = AuditLog.query.count()

                logger.info(f"✓ Database table counts:")
                logger.info(f"  - Users: {user_count}")
                logger.info(f"  - Transcriptions: {transcription_count}")
                logger.info(f"  - Translations: {translation_count}")
                logger.info(f"  - Audit Logs: {audit_log_count}")
            except Exception as e:
                logger.error(f"❌ Error checking tables: {str(e)}")

        logger.info("✓ SQLAlchemy models reset and initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error resetting SQLAlchemy models: {str(e)}")
        import traceback
        traceback.print_exc()
        return False