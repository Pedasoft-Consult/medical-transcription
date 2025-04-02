from http.server import BaseHTTPRequestHandler
from minimal_api import app


def get_flask_response():
    """Get a basic Flask response"""
    with app.test_client() as client:
        response = client.get('/')
        return response.get_data(), response.status_code


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get data from Flask app
        data, status_code = get_flask_response()

        # Return the response
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(data)
        return