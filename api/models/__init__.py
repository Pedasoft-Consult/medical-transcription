# api/models/__init__.py
import logging

logger = logging.getLogger(__name__)

# Track which models have been imported
_imported_models = set()


def import_all_models():
    """Import all models to register them with SQLAlchemy once"""
    global _imported_models

    # Only import models that haven't been imported yet
    if 'user' not in _imported_models:
        logger.info("Importing user model")
        from . import user
        _imported_models.add('user')

    if 'transcript' not in _imported_models:
        logger.info("Importing transcript model")
        from . import transcript
        _imported_models.add('transcript')

    if 'translation' not in _imported_models:
        logger.info("Importing translation model")
        from . import translation
        _imported_models.add('translation')

    if 'audit_log' not in _imported_models:
        logger.info("Importing audit_log model")
        from . import audit_log
        _imported_models.add('audit_log')

    return True