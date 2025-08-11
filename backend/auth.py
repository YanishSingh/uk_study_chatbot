from flask import Blueprint, request, jsonify, current_app
from models import db, User
import bcrypt
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validate
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    # Check uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, email=email, password_hash=pw_hash.decode('utf-8'))
    db.session.add(new_user)
    db.session.commit()

    token = create_token(new_user.id)
    return jsonify({
        'message': 'User registered successfully',
        'token': token,
        'username': new_user.username,
        'email': new_user.email,
        'user_id': new_user.id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_identifier = data.get('username') or data.get('email')  # Can be username or email
    password = data.get('password')

    if not user_identifier or not password:
        return jsonify({'error': 'Username/email and password are required'}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == user_identifier) | (User.email == user_identifier)
    ).first()

    if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        token = create_token(user.id)
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'username': user.username,
            'email': user.email,
            'user_id': user.id
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Profile endpoint to fetch the logged-in user's info
@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'user_id': current_user.id
    })
