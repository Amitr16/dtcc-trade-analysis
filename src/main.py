# src/main.py
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.trade_data import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dtcc-analysis-secret-key-2025')

# --- DB configuration (single source of truth) ---
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Prefer managed Postgres if provided
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    logger.info(f"[DB] Using PostgreSQL: {db_url}")
else:
    # SQLite with persistent disk if available
    db_dir = Path(os.environ.get("DB_DIR", "/var/data"))
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        # sanity write test (non-fatal)
        t = db_dir / ".rw_test"
        t.write_text("ok", encoding="utf-8")
        t.unlink(missing_ok=True)
        disk_ok = True
        logger.info(f"[DB] Using persistent disk: {db_dir}")
    except Exception as e:
        disk_ok = False
        # fallback to project dir if disk not mounted/writable yet
        db_dir = Path("/opt/render/project")
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"[DISK] /var/data not writable, falling back to {db_dir}: {e}")

    sqlite_path = db_dir / "app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app)
db.init_app(app)

# --- HEALTH ENDPOINT (for Render) ---
@app.get("/health")
def health():
    return jsonify(ok=True), 200

# Log the effective DB once app context is available
with app.app_context():
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    logger.info(f"[BOOT] DB URI: {uri}")

# Import routes/services AFTER db.init_app(app)
from src.routes.api_fixed import api_bp, init_data_processor
app.register_blueprint(api_bp, url_prefix="/api")

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

# Start background worker(s) inside app context
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