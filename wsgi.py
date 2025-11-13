"""
WSGI entry point for PythonAnywhere (or other mod_wsgi hosts).

This file imports the Flask app factory and creates the WSGI application object
that the server expects.
"""

import sys
from pathlib import Path
from backend.app import create_app

# Add your project directory to the sys.path
# PythonAnywhere typical path: /home/USERNAME/mycount
project_home = Path(__file__).resolve().parent
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

# Create the WSGI application
application = create_app()

# Optional: Set environment variables here if not using .env or PythonAnywhere
# os.environ.setdefault('SECRET_KEY', 'your-secret-key')
# os.environ.setdefault('DATABASE_URL', 'mysql://user:pass@host/db')
