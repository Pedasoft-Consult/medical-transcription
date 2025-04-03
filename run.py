"""
Run script for Medical Transcription App
"""
import os

# Clear SQLAlchemy mappers before initializing app
try:
    from sqlalchemy.orm import clear_mappers
    clear_mappers()
except ImportError:
    pass

from flask import jsonify
from api import create_app
from api.config import config

# Create the Flask application
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