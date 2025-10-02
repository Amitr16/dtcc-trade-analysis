#!/usr/bin/env python3
"""
Debug script to check database persistence in production
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_persistence():
    print("=== DATABASE PERSISTENCE DEBUG ===")
    
    # Check environment variables
    print(f"RENDER env var: {os.environ.get('RENDER')}")
    print(f"DB_DIR env var: {os.environ.get('DB_DIR')}")
    print(f"DATA_DIR env var: {os.environ.get('DATA_DIR')}")
    
    # Check if we're in Render
    is_render = bool(os.environ.get("RENDER"))
    print(f"Is Render environment: {is_render}")
    
    # Determine database path
    if is_render:
        db_dir = Path(os.environ.get("DB_DIR", "/var/data"))
        if not db_dir.exists():
            db_dir = Path("/opt/render/project")
        print(f"Render DB directory: {db_dir}")
        print(f"Render DB directory exists: {db_dir.exists()}")
        print(f"Render DB directory is writable: {os.access(db_dir, os.W_OK) if db_dir.exists() else False}")
    else:
        db_dir = Path(os.environ.get("DB_DIR", Path.cwd()))
        print(f"Local DB directory: {db_dir}")
        print(f"Local DB directory exists: {db_dir.exists()}")
        print(f"Local DB directory is writable: {os.access(db_dir, os.W_OK) if db_dir.exists() else False}")
    
    # Check database file
    db_path = db_dir / "app.db"
    print(f"Database file path: {db_path}")
    print(f"Database file exists: {db_path.exists()}")
    print(f"Database file size: {db_path.stat().st_size if db_path.exists() else 'N/A'} bytes")
    
    # Check if it's a persistent mount
    if is_render:
        print(f"Mount point /var/data exists: {Path('/var/data').exists()}")
        print(f"Mount point /var/data is writable: {os.access('/var/data', os.W_OK) if Path('/var/data').exists() else False}")
        
        # Check if it's actually mounted
        try:
            import subprocess
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if '/var/data' in result.stdout:
                print("✅ /var/data is mounted as a persistent disk")
            else:
                print("❌ /var/data is NOT mounted as a persistent disk")
        except Exception as e:
            print(f"Could not check mount status: {e}")
    
    # Test database creation
    try:
        from src.main import app
        with app.app_context():
            from src.models.trade_data import TradeRecord
            count = TradeRecord.query.count()
            print(f"Current trade count in database: {count}")
            
            # Check database URI
            uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            print(f"Database URI: {uri}")
            
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    check_database_persistence()
