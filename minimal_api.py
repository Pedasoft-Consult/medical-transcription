from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
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