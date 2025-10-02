"""
Production main.py for Render.com deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    from flask import Flask
    from flask_cors import CORS
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app)
    
    # Configure database
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Convert postgres:// to postgresql:// for SQLAlchemy
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///src/database/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db = SQLAlchemy(app)
    
    # Import models and routes
    from models.trade_data import TradeRecord, StructuredTrade, Commentary, ProcessingLog
    from routes.api_fixed import api_bp
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize database tables
    with app.app_context():
        try:
            # Ensure database directory exists
            import os
            db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
    
    return app, db

def init_data_processor(app):
    """Initialize the data processor for background tasks"""
    try:
        from services.data_processor import DataProcessor
        processor = DataProcessor(app)
        logger.info("Data processor initialized successfully")
        return processor
    except Exception as e:
        logger.error(f"Error initializing data processor: {e}")
        return None

# Create the app
app, db = create_app()

# Initialize data processor
processor = init_data_processor(app)

if __name__ == '__main__':
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
