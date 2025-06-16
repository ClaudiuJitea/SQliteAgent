from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
import sys
from config import config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__, template_folder='static')
    app.config.from_object(config[config_name])

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    # If you want to see SQLAlchemy logs, uncomment the following:
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,  # Change from 5 to 60 seconds
        ping_interval=25
    )
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.database import database_bp
    from app.routes.ai import ai_bp
    from app.routes.tables import tables_bp
    
    app.register_blueprint(database_bp, url_prefix='/api/databases')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(tables_bp, url_prefix='/api/tables')
    
    # Initialize WebSocket handlers
    from app.websocket.handlers import init_socketio_handlers
    init_socketio_handlers(socketio)
    
    # Auto-load existing databases from uploads folder
    def auto_load_databases():
        from app.models.database import DatabaseModel
        db_model = DatabaseModel()
        upload_folder = app.config['UPLOAD_FOLDER']
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                    file_path = os.path.join(upload_folder, filename)
                    try:
                        db_model.load_database(file_path)
                        app.logger.info(f"Auto-loaded database: {filename}")
                    except Exception as e:
                        app.logger.error(f"Failed to auto-load database {filename}: {str(e)}")
    
    # Load databases after app initialization
    with app.app_context():
        auto_load_databases()
    
    # Main route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)