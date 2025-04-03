"""
Redis compatibility module for different Flask-Limiter versions

This module provides a compatibility layer for accessing the RedisStorage class
across different versions of Flask-Limiter.
"""
import logging

logger = logging.getLogger(__name__)


def get_redis_storage():
    """
    Get the appropriate RedisStorage class based on the installed flask-limiter version

    Returns:
        RedisStorage class or None if not available
    """
    # Try the newer location first (Flask-Limiter >= 3.0.0)
    try:
        from flask_limiter.util import storage
        if hasattr(storage, 'RedisStorage'):
            logger.debug("Using RedisStorage from flask_limiter.util.storage")
            return storage.RedisStorage
    except (ImportError, AttributeError):
        logger.debug("Could not import RedisStorage from flask_limiter.util.storage")
        pass

    # Try other possible locations
    try:
        from flask_limiter.util import RedisStorage
        logger.debug("Using RedisStorage from flask_limiter.util")
        return RedisStorage
    except ImportError:
        logger.debug("Could not import RedisStorage from flask_limiter.util")
        pass

    # Try the older location (Flask-Limiter < 3.0.0)
    try:
        from flask_limiter.storage import RedisStorage
        logger.debug("Using RedisStorage from flask_limiter.storage")
        return RedisStorage
    except ImportError:
        logger.debug("Could not import RedisStorage from flask_limiter.storage")
        pass

    # Try the limits package directly
    try:
        from limits.storage import RedisStorage
        logger.debug("Using RedisStorage from limits.storage")
        return RedisStorage
    except ImportError:
        logger.error("Could not import RedisStorage from any location")
        return None