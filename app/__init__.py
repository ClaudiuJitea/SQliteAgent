from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

def create_app(config_name=None):
    """Application factory pattern"""
    from config import config
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app, socketio