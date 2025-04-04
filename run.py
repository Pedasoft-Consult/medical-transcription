"""
Run script for Medical Transcription App
"""
import os
import logging

# Try to clear SQLAlchemy mappers before loading any models
try:
    from sqlalchemy.orm import clear_mappers
    clear_mappers()
    print("SQLAlchemy mappers cleared")
except ImportError:
    print("Could not import clear_mappers from sqlalchemy.orm")
    pass

# Create the Flask application
from flask import jsonify
from api import create_app
from api.config import config

# Create the application
app = create_app()

@app.route("/api/", methods=["GET"])
def home():
    return jsonify({
        "message": "Medical Transcription API",
        "status": "running"
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })

if __name__ == "__main__":
    # Get port from config or environment
    port = int(os.environ.get("PORT", config.get_port()))

    # Get debug mode from config or environment
    debug = os.environ.get("DEBUG", config.get_debug())
    if isinstance(debug, str):
        debug = debug.lower() in ('true', '1', 't', 'y', 'yes')

    # Run the app
    app.run(host="0.0.0.0", port=port, debug=debug)