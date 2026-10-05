import os
import sys

# Compute project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app

# Ensure templates and static directories are set accurately on Vercel
tmpl_path = os.path.join(BASE_DIR, 'templates')
if not os.path.exists(tmpl_path):
    tmpl_path = os.path.join(BASE_DIR, 'frontend', 'templates')
app.template_folder = tmpl_path

stc_path = os.path.join(BASE_DIR, 'static')
if not os.path.exists(stc_path):
    stc_path = os.path.join(BASE_DIR, 'frontend', 'static')
app.static_folder = stc_path

# Export WSGI app for Vercel
app.debug = False

if __name__ == '__main__':
    app.run()
