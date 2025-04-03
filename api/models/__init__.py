# Update api/models/__init__.py to use a singleton pattern

"""
Models package for SQLAlchemy models
"""
import logging

logger = logging.getLogger(__name__)


# Store model classes in a registry to avoid duplicate registration
class ModelRegistry:
    _models = {}

    @classmethod
    def register(cls, model_name, model_class=None):
        """Register a model only if it hasn't been registered before"""
        # If model_class is None, assume the first argument is the model class itself
        if model_class is None:
            model_class = model_name
            model_name = model_class.__name__

        if model_name not in cls._models:
            cls._models[model_name] = model_class
            logger.info(f"Registered model: {model_name}")
            return model_class
        logger.info(f"Using existing registered model: {model_name}")
        return cls._models[model_name]


# Empty _models to avoid exposing any imports
__all__ = []