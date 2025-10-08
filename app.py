"""
Moulya College Management System
Main Flask application entry point
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import Config
from database import db, init_db

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Add CSRF token to template context
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.management import management_bp
    from routes.lecturer import lecturer_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(management_bp, url_prefix='/management')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    
    # Initialize database
    init_db(app)
    
    # Jinja filter: format numbers so 34.0 -> 34, keep 34.5 as 34.5
    @app.template_filter('format_mark')
    def format_mark(value):
        try:
            # Handle None or empty gracefully
            if value is None or value == "":
                return ""
            number = float(value)
            # If it's an integer value (like 34.0), return without decimals
            if number.is_integer():
                return str(int(number))
            # Otherwise, return as minimal float string (avoids trailing zeros)
            # Using rstrip to avoid cases like '34.500000'
            text = ("%s" % number)
            # Normalize scientific notation if any
            if 'e' in text or 'E' in text:
                text = ("%.15f" % number).rstrip('0').rstrip('.')
            return text
        except Exception:
            # Fallback to original value if not a number
            return value
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)

