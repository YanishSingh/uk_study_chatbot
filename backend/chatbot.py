import json
import os
from datetime import datetime
from flask import request, jsonify, current_app, Blueprint
from models import db, User, ChatSession, ChatHistory
from auth import token_required
import openai
import requests

chatbot_bp = Blueprint('chatbot', __name__)

# --- Load data files for Rasa actions to use ---
DATA_PATH = os.path.join(os.path.dirname(__file__), 'university_data', 'uk_universities_chatbot_ready.json')
UK_CHECKLIST_PATH = os.path.join(os.path.dirname(__file__), 'university_data', 'uk_checklist.json')

# Load data (keeping for Rasa actions and fallback responses)
try:
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        universities = json.load(f)
except FileNotFoundError:
    universities = []
    print("Warning: University data file not found")

try:
    with open(UK_CHECKLIST_PATH, 'r', encoding='utf-8') as f:
        uk_checklist_data = json.load(f)
except FileNotFoundError:
    uk_checklist_data = {}
    print("Warning: UK checklist data file not found")

# --- Utility Functions ---
def generate_chat_name(question: str):
    """Generate a meaningful name for chat sessions"""
    if not question or not question.strip():
        return "New Chat"
    words = question.strip().split()
    name = " ".join(words[:6])
    if len(words) > 6:
        name += "..."
    return name.capitalize()

def get_openai_client():
    """Get OpenAI client instance"""
    return openai.OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

def query_rasa(message: str, sender_id: str = "user"):
    """Send message to Rasa and get response"""
    try:
        rasa_url = "http://localhost:5005/webhooks/rest/webhook"
        payload = {
            "sender": sender_id,
            "message": message
        }
        
        response = requests.post(rasa_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            rasa_responses = response.json()
            if rasa_responses:
                # Combine multiple responses from Rasa if any
                combined_response = "\n\n".join([resp.get("text", "") for resp in rasa_responses if resp.get("text")])
                return combined_response if combined_response.strip() else None
        
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Rasa: {e}")
        return None

def get_chatgpt_response(message: str):
    """Get response from ChatGPT as fallback"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant specializing in UK university applications for international students. Provide accurate, helpful information about UK universities, application processes, visa requirements, and student life."
                },
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting ChatGPT response: {e}")
        return f"I apologize, but I'm having trouble processing your request right now. Please try again later."

# --- Session Management Endpoints ---
@chatbot_bp.route('/sessions', methods=['GET'])
@token_required
def list_sessions(current_user):
    """Get all chat sessions for the current user"""
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()
    return jsonify([
        {'id': s.id, 'name': s.name, 'created_at': s.created_at}
        for s in sessions
    ])

@chatbot_bp.route('/sessions', methods=['POST'])
@token_required
def create_session(current_user):
    """Create a new chat session"""
    data = request.get_json() or {}
    message = data.get('message', '').strip() if data.get('message') else ''
    name = generate_chat_name(message) if message else "New Chat"
    
    session = ChatSession(user_id=current_user.id, name=name)
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'id': session.id, 'name': name})

@chatbot_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
@token_required
def get_session_messages(current_user, session_id):
    """Get all messages for a specific session"""
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    messages = ChatHistory.query.filter_by(
        session_id=session_id, 
        user_id=current_user.id
    ).order_by(ChatHistory.timestamp).all()
    
    return jsonify([
        {
            'id': m.id,
            'message': m.message,
            'response': m.response,
            'timestamp': m.timestamp
        }
        for m in messages
    ])

@chatbot_bp.route('/sessions/<int:session_id>/message', methods=['POST'])
@token_required
def add_message(current_user, session_id):
    """Add a new message to a session and get AI response"""
    data = request.get_json()
    message = data.get('message')
    
    if not message or not message.strip():
        return jsonify({'error': 'Message required'}), 400

    # Update session name if it's a new chat
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
        
    if session.name == "New Chat" or not session.name.strip():
        session.name = generate_chat_name(message)
        db.session.commit()

    # Try Rasa first for structured responses
    response = query_rasa(message, sender_id=str(current_user.id))
    
    # If Rasa doesn't have a response, use ChatGPT
    if not response:
        response = get_chatgpt_response(message)

    # Save the conversation to database
    chat_msg = ChatHistory(
        session_id=session_id,
        user_id=current_user.id,
        message=message.strip(),
        response=response
    )
    db.session.add(chat_msg)
    db.session.commit()
    
    return jsonify({'answer': response})

@chatbot_bp.route('/sessions', methods=['DELETE'])
@token_required
def delete_all_sessions(current_user):
    """Delete all sessions for the current user"""
    # Delete chat histories first (to avoid foreign key error)
    sessions = ChatSession.query.filter_by(user_id=current_user.id).all()
    for session in sessions:
        ChatHistory.query.filter_by(session_id=session.id).delete()
    ChatSession.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({'message': 'All sessions deleted.'}), 200

# --- Data Access Endpoints (for frontend/Rasa actions) ---
@chatbot_bp.route('/uk_checklist', methods=['GET'])
def get_uk_checklist():
    """Get the complete UK checklist data"""
    return jsonify(uk_checklist_data)

@chatbot_bp.route('/uk_checklist/<section>', methods=['GET'])
def get_uk_checklist_section(section):
    """Get a specific section from UK checklist data"""
    checklist = uk_checklist_data.get("uk_application_checklist", {})
    costing = uk_checklist_data.get("uk_costing_info", {})
    section_data = checklist.get(section) or costing.get(section)
    
    if section_data is None:
        return jsonify({"error": f"Section '{section}' not found."}), 404
    
    return jsonify({section: section_data})

# --- Legacy Endpoints (kept for backward compatibility, but simplified) ---
@chatbot_bp.route('/history', methods=['GET'])
@token_required
def chat_history(current_user):
    """Get recent chat history (legacy endpoint)"""
    chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(20).all()
    history = [
        {
            'message': c.message,
            'response': c.response,
            'timestamp': c.timestamp
        } for c in chats
    ]
    return jsonify(history)

@chatbot_bp.route('/ask_gpt', methods=['POST'])
@token_required
def ask_gpt(current_user):
    """Direct ChatGPT query (legacy endpoint)"""
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question required'}), 400

    # Try Rasa first, then ChatGPT
    answer = query_rasa(question, sender_id=str(current_user.id))
    if not answer:
        answer = get_chatgpt_response(question)

    # Save to history
    history = ChatHistory(
        session_id=None,  # Legacy support
        user_id=current_user.id,
        message=question,
        response=answer
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'answer': answer})
