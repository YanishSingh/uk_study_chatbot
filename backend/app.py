from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config
from models import db
from auth import auth_bp
from chatbot import chatbot_bp
import os
from dotenv import load_dotenv

# Load .env from backend folder
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

@app.route("/", methods=["GET"])
def home():
    return {"message": "UK Study Chatbot Backend is running!"}

# Initialize database tables
with app.app_context():
    db.create_all()
    print("🗄️  Database tables initialized!")

if __name__ == "__main__":
    app.run(debug=True)
