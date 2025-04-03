"""
Database connection setup
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base model class
db = SQLAlchemy(model_class=Base)

# Clear any previously registered models to avoid conflicts
def clear_mappers():
    """Clear all registered mappers to avoid conflicts"""
    import sqlalchemy.orm
    sqlalchemy.orm.clear_mappers()