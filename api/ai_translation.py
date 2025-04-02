"""
AI Translation module for Medical Transcription App
Uses external translation APIs to avoid size limitations
"""
import os
import requests
from flask import Blueprint, request, jsonify

# Create Blueprint for translation routes
translation_bp = Blueprint('translation', __name__)

# API keys from environment variables for security
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY')
GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')


@translation_bp.route('/api/ai_translation', methods=['POST'])
def translate_text():
    """
    Translate medical text using external API (DeepL or Google)
    """
    # Get request data
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({
            "error": "No text provided for translation",
            "status": "failed"
        }), 400

    text = data.get('text', '')
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
    is_medical = data.get('medical', True)

    # Validate input
    if not text:
        return jsonify({
            "error": "Empty text provided",
            "status": "failed"
        }), 400

    try:
        # Choose the appropriate translation service
        # DeepL is better for medical content when available
        if DEEPL_API_KEY and target_lang in get_deepl_supported_languages():
            result = translate_with_deepl(text, source_lang, target_lang)
        else:
            # Fallback to Google Translate
            result = translate_with_google(text, source_lang, target_lang)

        return jsonify({
            "status": "success",
            "original_text": text,
            "translated_text": result.get('translated_text', ''),
            "source_language": result.get('detected_source_language', source_lang),
            "target_language": target_lang
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "failed"
        }), 500


def translate_with_deepl(text, source_lang='auto', target_lang='en'):
    """Translate text using DeepL API"""
    url = "https://api.deepl.com/v2/translate"

    # Map source language to DeepL format if needed
    if source_lang != 'auto':
        source_lang = source_lang.upper()

    # Map target language to DeepL format
    target_lang = target_lang.upper()

    # Prepare request data
    data = {
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'target_lang': target_lang,
    }

    # Add source language if not auto
    if source_lang != 'auto':
        data['source_lang'] = source_lang

    response = requests.post(url, data=data)

    if response.status_code == 200:
        translation = response.json()
        return {
            'translated_text': translation['translations'][0]['text'],
            'detected_source_language': translation['translations'][0]['detected_source_language']
        }
    else:
        raise Exception(f"DeepL translation failed: {response.text}")


def translate_with_google(text, source_lang='auto', target_lang='en'):
    """Translate text using Google Translate API"""
    url = "https://translation.googleapis.com/language/translate/v2"

    params = {
        'key': GOOGLE_TRANSLATE_API_KEY,
        'q': text,
        'target': target_lang,
    }

    # Add source language if not auto
    if source_lang != 'auto':
        params['source'] = source_lang

    response = requests.post(url, params=params)

    if response.status_code == 200:
        translation = response.json()
        return {
            'translated_text': translation['data']['translations'][0]['translatedText'],
            'detected_source_language': translation['data']['translations'][0].get('detectedSourceLanguage',
                                                                                   source_lang)
        }
    else:
        raise Exception(f"Google translation failed: {response.text}")


def get_deepl_supported_languages():
    """Return list of languages supported by DeepL API"""
    # This could fetch from API, but for simplicity we hardcode common languages
    return ['EN', 'DE', 'FR', 'ES', 'IT', 'NL', 'PL', 'PT', 'RU', 'JA', 'ZH']