# Import all models in a controlled way with a function
_models_imported = False

def import_all_models():
    """Import all models to register them with SQLAlchemy"""
    global _models_imported
    if not _models_imported:
        # Import models only once
        from . import user, transcript, translation, audit_log
        _models_imported = True
        return True
    return False