"""
Main application entry point for Medical Transcription App
"""
import os
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, jsonify, request

# Import blueprints only if they exist
try:
    from api.ai_transcription import transcription_bp
    from api.ai_translation import translation_bp

    HAS_BLUEPRINTS = True
except ImportError:
    HAS_BLUEPRINTS = False

# Create the Flask application
app = Flask(__name__)

# Register blueprints if they exist
if HAS_BLUEPRINTS:
    app.register_blueprint(transcription_bp)
    app.register_blueprint(translation_bp)


# Root route
@app.route('/')
def home():
    return jsonify({
        "message": "Medical Transcription App",
        "status": "running",
        "available_routes": [
            "/api/ai_transcription",
            "/api/ai_translation"
        ]
    }), 200


# Default route to handle all requests
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/') and not (
            path.startswith('api/ai_transcription') or
            path.startswith('api/ai_translation')):
        return jsonify({
            "error": "Endpoint not found",
            "path": path,
            "status": "failed"
        }), 404

    return home()


# Vercel serverless function handler
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response = app.dispatch_request()
        self.wfile.write(response.get_data())
        return

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len)

        # Set environment variables for Flask
        os.environ['REQUEST_METHOD'] = 'POST'
        os.environ['CONTENT_TYPE'] = self.headers.get('Content-Type', '')
        os.environ['CONTENT_LENGTH'] = str(content_len)

        # Handle the request
        response = app.dispatch_request()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.get_data())
        return


if __name__ == "__main__":
    # Run locally
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)