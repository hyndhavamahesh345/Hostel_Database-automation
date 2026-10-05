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

# Export WSGI app handlers for Vercel
app.debug = False

class VercelPathFix:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Vercel rewrites PATH_INFO to the destination (e.g., /api/index)
        # We can restore the original path by stripping the rewrite if needed, 
        # but typically Vercel provides HTTP_X_Vercel_Forwarded_For or we just use Werkzeug's capabilities.
        # Actually, Vercel sets the original path in HTTP_X_NOW_ROUTE_MATCHES or x-now-route-matches or HTTP_X_FORWARDED_PATH
        
        # Safe fallback: if PATH_INFO is exactly '/api/index', we assume it's meant for '/' if it was a rewrite, 
        # but to be robust for all routes like /login, Vercel sets HTTP_X_NOW_ROUTE_MATCHES
        # A simpler way in Vercel is to just check the request URI
        request_uri = environ.get('REQUEST_URI', environ.get('RAW_URI'))
        if request_uri:
            environ['PATH_INFO'] = request_uri.split('?')[0]
            
        return self.app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
handler = app
application = app

if __name__ == '__main__':
    app.run()
