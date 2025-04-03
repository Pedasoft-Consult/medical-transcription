"""
Authentication routes for user registration, login, and profile management
"""
from datetime import timedelta
from flask import Blueprint, request, jsonify, g, current_app
from ..utils.rate_limiter import get_rate_limit
from ..db import db

# Import models directly from their modules
from ..models.user import User
from ..security import token_required, create_access_token

# Create blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json

        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'message': 'Missing required fields'}), 400

        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already registered'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'Username already taken'}), 400

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        import traceback
        error_details = str(e) + "\n" + traceback.format_exc()
        print(f"Registration error: {error_details}")  # This will appear in Vercel logs
        return jsonify({
            'message': f'Server error: {str(e)}',
            'details': error_details
        }), 500


@auth_bp.route('/token', methods=['POST'])
def login():
    """Login and get access token"""
    # Apply rate limiting using app.limiter
    limiter = current_app.limiter
    limiter.limit(get_rate_limit("auth.token"))(lambda: None)()

    # FastAPI OAuth2 form compatibility
    username = request.form.get('username')  # This is actually the email in our case
    password = request.form.get('password')

    # If not form data, try JSON
    if not username or not password:
        data = request.json
        if data:
            username = data.get('username')
            password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing email or password'}), 400

    # Find user by email
    user = User.query.filter_by(email=username).first()

    # Check password
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Generate token
    access_token_expires = timedelta(minutes=30)  # Using value from the security module
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer'
    })


@auth_bp.route('/users/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user profile"""
    user = g.current_user
    return jsonify(user.to_dict())


@auth_bp.route('/ping', methods=['GET'])
def ping():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "message": "API is running"}), 200
