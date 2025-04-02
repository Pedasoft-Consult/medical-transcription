"""
AI Transcription module for Medical Transcription App
Uses external APIs for speech-to-text to avoid size limitations
"""
import os
import requests
from flask import Blueprint, request, jsonify

# Create Blueprint for transcription routes
transcription_bp = Blueprint('transcription', __name__)

# API keys from environment variables for security
ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')


@transcription_bp.route('/api/ai_transcription', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio using external API (AssemblyAI)
    """
    # Check if file was provided in request
    if 'audio' not in request.files:
        return jsonify({
            "error": "No audio file provided",
            "status": "failed"
        }), 400

    audio_file = request.files['audio']

    # Validate file
    if audio_file.filename == '':
        return jsonify({
            "error": "Empty file provided",
            "status": "failed"
        }), 400

    # Get transcription options from request
    options = request.form.to_dict()
    language = options.get('language', 'en')
    is_medical = options.get('medical', 'true').lower() == 'true'

    try:
        # For demonstration, we'll use AssemblyAI which has medical transcription
        # Upload the file to AssemblyAI
        upload_url = upload_to_assemblyai(audio_file)

        # Start transcription job
        transcript_id = start_assemblyai_transcription(upload_url, language, is_medical)

        # Get transcription result (this would normally be async)
        result = get_assemblyai_result(transcript_id)

        return jsonify({
            "status": "success",
            "transcription": result.get('text', ''),
            "confidence": result.get('confidence', 0),
            "words": result.get('words', [])
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "failed"
        }), 500


def upload_to_assemblyai(audio_file):
    """Upload audio file to AssemblyAI and return upload URL"""
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                             headers=headers,
                             data=audio_file)

    if response.status_code == 200:
        return response.json()['upload_url']
    else:
        raise Exception(f"Upload failed: {response.text}")


def start_assemblyai_transcription(audio_url, language='en', is_medical=True):
    """Start transcription job with AssemblyAI"""
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }

    json_data = {
        "audio_url": audio_url,
        "language_code": language
    }

    # Add medical domain for better accuracy if requested
    if is_medical:
        json_data["vocabulary_id"] = "medical"

    response = requests.post('https://api.assemblyai.com/v2/transcript',
                             headers=headers,
                             json=json_data)

    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"Transcription start failed: {response.text}")


def get_assemblyai_result(transcript_id):
    """
    Get transcription result from AssemblyAI
    In a production app, this would be done asynchronously with a webhook
    """
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    while True:
        response = requests.get(polling_endpoint, headers=headers)
        response_json = response.json()

        if response_json['status'] == 'completed':
            return response_json
        elif response_json['status'] == 'error':
            raise Exception(f"Transcription failed: {response_json['error']}")

        # In a real app, this would use async pattern instead of polling
        # For demo only - don't use in production
        import time
        time.sleep(3)