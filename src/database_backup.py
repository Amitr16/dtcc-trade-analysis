#!/usr/bin/env python3
"""
Database backup utility for production persistence
"""
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def backup_database(db_path, backup_dir=None):
    """Create a backup of the database before any operations"""
    try:
        if not Path(db_path).exists():
            logger.info("No database to backup")
            return None
            
        if backup_dir is None:
            backup_dir = Path(db_path).parent / "backups"
        
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"app_backup_{timestamp}.db"
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None

def restore_database(backup_path, db_path):
    """Restore database from backup"""
    try:
        if not Path(backup_path).exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
            
        # Create backup of current database first
        if Path(db_path).exists():
            backup_database(db_path)
        
        # Restore from backup
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"Database restored from: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        return False

def check_database_integrity(db_path):
    """Check if database is valid and not corrupted"""
    try:
        if not Path(db_path).exists():
            return False, "Database file does not exist"
            
        # Try to open and query the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            return False, "No tables found in database"
            
        # Check if we can query trade_records table
        cursor.execute("SELECT COUNT(*) FROM trade_records LIMIT 1;")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return True, f"Database is valid with {count} trade records"
        
    except Exception as e:
        return False, f"Database integrity check failed: {e}"

if __name__ == "__main__":
    # Test the backup functionality
    import sys
    from src.main import app
    
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")
            print(f"Checking database: {db_path}")
            
            is_valid, message = check_database_integrity(db_path)
            print(f"Database integrity: {is_valid} - {message}")
            
            if is_valid:
                backup_path = backup_database(db_path)
                if backup_path:
                    print(f"Backup created: {backup_path}")
            else:
                print("Database is corrupted, cannot create backup")
