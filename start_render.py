#!/usr/bin/env python3
"""
Startup script for Render.com deployment
Handles environment setup and application startup
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

def setup_environment():
    """Set up environment for Render deployment"""
    try:
        # Ensure required directories exist
        os.makedirs('src/database', exist_ok=True)
        os.makedirs('src/static', exist_ok=True)
        
        # Set Flask environment
        os.environ.setdefault('FLASK_ENV', 'production')
        
        # Set database URL if not already set
        if not os.getenv('DATABASE_URL'):
            # Use SQLite for local development fallback
            os.environ['DATABASE_URL'] = 'sqlite:///src/database/app.db'
        
        logger.info("Environment setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("Starting DTCC Trade Analysis Application on Render...")
    
    # Setup environment
    if not setup_environment():
        logger.error("Failed to setup environment")
        sys.exit(1)
    
    # Import and run the Flask app
    try:
        from main import app, init_data_processor
        
        # Initialize data processor
        init_data_processor(app)
        
        # Get port from Render environment
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting Flask application on port {port}")
        
        # Run the application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False
        )
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
