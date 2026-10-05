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
        from urllib.parse import parse_qs
        
        # Check if we explicitly passed the path via query string in vercel.json rewrites
        qs = environ.get('QUERY_STRING', '')
        params = parse_qs(qs, keep_blank_values=True)
        
        if '__vercel_path' in params:
            # We explicitly mapped the path, e.g. /api/index?__vercel_path=login
            # If the user visits the root '/', the parameter will be empty, which is correct!
            path_val = params['__vercel_path'][0]
            if not path_val.startswith('/'):
                path = '/' + path_val
            else:
                path = path_val
            environ['PATH_INFO'] = path
        else:
            # Fallback to standard HTTP headers if available
            original_uri = environ.get('REQUEST_URI', environ.get('RAW_URI'))
            if original_uri:
                path = original_uri.split('?')[0]
                environ['PATH_INFO'] = path
                
        return self.app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
handler = app
application = app

if __name__ == '__main__':
    app.run()
