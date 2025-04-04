"""
Check SQLAlchemy model registration and fix any issues
"""
import os
import sys
import inspect
import sqlalchemy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def check_sqlalchemy_models():
    """Check all SQLAlchemy models for registration issues"""
    print("🔍 Checking SQLAlchemy models for registration issues...")

    # Try to clear mappers first
    try:
        from sqlalchemy.orm import clear_mappers
        clear_mappers()
        print("✅ Successfully cleared existing SQLAlchemy mappers")
    except ImportError:
        print("⚠️ Could not import clear_mappers from sqlalchemy.orm")
        pass

    # Import models carefully
    print("\nImporting models:")
    models = {}
    registration_issues = []

    try:
        print("  - Setting up Flask app context...")
        from api import create_app
        app = create_app()

        with app.app_context():
            print("  - Importing User model...")
            from api.models.user import User
            models['User'] = User

            print("  - Importing Transcription model...")
            from api.models.transcript import Transcription
            models['Transcription'] = Transcription

            print("  - Importing Translation model...")
            from api.models.translation import Translation
            models['Translation'] = Translation

            print("  - Importing AuditLog model...")
            from api.models.audit_log import AuditLog
            models['AuditLog'] = AuditLog

            # Check for db configuration
            from api.db import db
            print(f"  - SQLAlchemy database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")

            # Check if tables exist
            db_tables = {}
            try:
                print("\nChecking model table registration:")
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                db_tables = inspector.get_table_names()

                for model_name, model_class in models.items():
                    table_name = model_class.__tablename__
                    if table_name in db_tables:
                        print(f"  ✅ {model_name} table '{table_name}' is registered in the database")
                    else:
                        print(f"  ❌ {model_name} table '{table_name}' is NOT registered in the database")
                        registration_issues.append(f"Table '{table_name}' for model {model_name} not found in database")
            except Exception as e:
                print(f"  ❌ Error checking tables: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        registration_issues.append(str(e))

    # Print summary
    print("\n=== SQLAlchemy Model Check Summary ===")
    if not registration_issues:
        print("✅ No SQLAlchemy model registration issues detected")
    else:
        print(f"❌ Found {len(registration_issues)} issues:")
        for i, issue in enumerate(registration_issues):
            print(f"  {i + 1}. {issue}")

    # Provide recommendations
    print("\n=== Recommendations ===")
    if registration_issues:
        print("1. Ensure all model classes have __table_args__ = {'extend_existing': True}")
        print("2. Clear SQLAlchemy mappers before initializing the app")
        print("3. Make sure models are imported in the correct order")
        print("4. Check for circular imports in your model files")
        print("5. Try running with FLASK_DEBUG=0 to avoid duplicate registration on reload")
    else:
        print("Your SQLAlchemy model registration looks good!")
        print("If you still have issues, try running the app with FLASK_DEBUG=0 to")
        print("prevent auto-reload from causing duplicate registration.")

    return len(registration_issues)


if __name__ == "__main__":
    sys.exit(check_sqlalchemy_models())