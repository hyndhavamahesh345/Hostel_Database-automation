import os
import shutil
import tempfile
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
    
    # Base directory & Vercel detection
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
    
    # SQLite Database File: Writable directory on serverless
    if IS_VERCEL:
        temp_dir = tempfile.gettempdir()
        SQLITE_DB_PATH = os.path.join(temp_dir, 'hostel_management.db')
        
        # Copy seeded database to temp_dir if not present
        if not os.path.exists(SQLITE_DB_PATH):
            src_candidates = [
                os.path.join(BASE_DIR, 'hostel_management.db'),
                os.path.join(BASE_DIR, 'backend', 'hostel_management.db'),
                os.path.join(os.path.dirname(BASE_DIR), 'hostel_management.db')
            ]
            for src in src_candidates:
                if os.path.exists(src):
                    try:
                        shutil.copy2(src, SQLITE_DB_PATH)
                        break
                    except Exception:
                        pass
    else:
        SQLITE_DB_PATH = os.path.join(BASE_DIR, 'hostel_management.db')
    
    # Preferred Engine ('mysql' or 'sqlite' or 'auto')
    DB_ENGINE = os.environ.get('DB_ENGINE', 'auto')
