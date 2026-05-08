import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-ai-mining-2024'
    
    # Render uses postgres:// but SQLAlchemy requires postgresql://
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    EXPORT_FOLDER = os.path.join(os.getcwd(), 'exports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # JWT Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Security
    SESSION_COOKIE_SECURE = True if os.environ.get('DATABASE_URL') else False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
