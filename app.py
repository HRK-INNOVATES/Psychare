import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "counseling_system_secret_key_8675309_secure_strong_key"
app.config['WTF_CSRF_TIME_LIMIT'] = 3600*24
app.config['WTF_CSRF_SSL_STRICT'] = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Ensure instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Use SQLite for local development
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'psychcare.db')
    database_url = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)

# Create tables
with app.app_context():
    import models
    db.create_all()
    logging.info("Database tables created")

from auth import *
from routes import *

if __name__ == '__main__':
    app.run(debug=True)
