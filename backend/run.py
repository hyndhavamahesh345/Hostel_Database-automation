"""
Woxsen University Hostel Accommodation and Student Services Management System
Root Application Entry Point
"""
import os
import sys

# Add backend directory to Python path
BACKEND_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app

if __name__ == '__main__':
    print("==========================================================")
    print(" WOXSEN UNIVERSITY HOSTEL MANAGEMENT SYSTEM ")
    print("==========================================================")
    print(" * Backend: Python Flask / MySQL / SQLite Dual Engine")
    print(" * Frontend: HTML5, Modern Glassmorphism CSS, Vanilla JS")
    print(" * Server running at: http://127.0.0.1:5000")
    print("==========================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
