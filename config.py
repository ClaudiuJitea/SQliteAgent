import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    OPENROUTER_MODEL = "google/gemini-2.5-flash-preview-05-20"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Database settings
    MAX_DATABASE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'.db', '.sqlite', '.sqlite3'}
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}