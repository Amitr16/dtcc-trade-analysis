import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.trade_data import db
from src.routes.api_fixed import api_bp, init_data_processor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configure app for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dtcc-analysis-secret-key-2025')

# Prefer DATABASE_URL if provided (Render Postgres etc)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Render/Heroku style compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local/dev fallback (persisted disk path on Render if you really want SQLite)
    # Use the mounted disk path so it survives restarts:
    #   render.yaml mounts /opt/render/project
    sqlite_path = os.environ.get('SQLITE_PATH', '/opt/render/project/data/app.db')
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{sqlite_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app)

# Initialize DB BEFORE importing/registering routes
db.init_app(app)

# Import routes AFTER db is initialized
from src.routes.api_fixed import api_bp, init_data_processor

# Register API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

# Initialize and start the automatic scheduler
with app.app_context():
    scheduler = init_data_processor(app)
    if scheduler:
        logger.info("🔄 AUTOMATIC SCHEDULER STARTED - Scripts will run every 60 seconds")
        logger.info("📊 DTCCParser.py + DTCCAnalysis.py will execute automatically")
    else:
        logger.error("❌ Failed to start automatic scheduler")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.errorhandler(404)
def not_found(error):
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return {"error": "Internal server error"}, 500

if __name__ == '__main__':
    logger.info("🚀 Starting DTCC Analysis Web Application...")
    logger.info("⏰ Background automation: DTCCParser + DTCCAnalysis every 60 seconds")
    app.run(host='0.0.0.0', port=5000, debug=False)

