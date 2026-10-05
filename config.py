import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hostel_management_secret_key_2026_dbms_jwt_secure')
    
    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'hostel_management')
    
    # Fallback SQLite Database file
    SQLITE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'hostel_management.db')
    
    # Preferred Engine ('mysql' or 'sqlite' or 'auto')
    DB_ENGINE = os.environ.get('DB_ENGINE', 'auto')
