#!/usr/bin/env python3
"""
Export raw trade history from database to CSV
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.trade_data import db, TradeRecord, StructuredTrade, Commentary, ProcessingLog
from flask import Flask

def create_app():
    """Create Flask app for database access"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def export_trade_records():
    """Export raw trade records to CSV"""
    app = create_app()
    
    with app.app_context():
        # Query all trade records
        trade_records = TradeRecord.query.all()
        
        if not trade_records:
            print("No trade records found in database")
            return False
        
        # Convert to list of dictionaries
        data = [record.to_dict() for record in trade_records]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        filename = f"raw_trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"Exported {len(trade_records)} trade records to {filename}")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['trade_time'].min()} to {df['trade_time'].max()}")
        print(f"Currencies: {df['currency'].unique()}")
        
        return True

def export_structured_trades():
    """Export structured trades to CSV"""
    app = create_app()
    
    with app.app_context():
        # Query all structured trades
        structured_trades = StructuredTrade.query.all()
        
        if not structured_trades:
            print("No structured trades found in database")
            return False
        
        # Convert to list of dictionaries
        data = [trade.to_dict() for trade in structured_trades]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        filename = f"structured_trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"Exported {len(structured_trades)} structured trades to {filename}")
        print(f"Columns: {list(df.columns)}")
        print(f"Structures: {df['structure'].value_counts().to_dict()}")
        
        return True

def export_commentaries():
    """Export commentaries to CSV"""
    app = create_app()
    
    with app.app_context():
        # Query all commentaries
        commentaries = Commentary.query.all()
        
        if not commentaries:
            print("No commentaries found in database")
            return False
        
        # Convert to list of dictionaries
        data = [commentary.to_dict() for commentary in commentaries]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        filename = f"commentary_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"Exported {len(commentaries)} commentaries to {filename}")
        print(f"Columns: {list(df.columns)}")
        print(f"Currencies: {df['currency'].unique()}")
        
        return True

def export_processing_logs():
    """Export processing logs to CSV"""
    app = create_app()
    
    with app.app_context():
        # Query all processing logs
        logs = ProcessingLog.query.all()
        
        if not logs:
            print("No processing logs found in database")
            return False
        
        # Convert to list of dictionaries
        data = [log.to_dict() for log in logs]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        filename = f"processing_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"Exported {len(logs)} processing logs to {filename}")
        print(f"Columns: {list(df.columns)}")
        print(f"Status counts: {df['status'].value_counts().to_dict()}")
        
        return True

def main():
    """Main export function"""
    print("=== DTCC Trade History Export ===")
    print(f"Exporting at: {datetime.now()}")
    print()
    
    # Export all data types
    success = True
    
    print("1. Exporting raw trade records...")
    if not export_trade_records():
        success = False
    
    print("\n2. Exporting structured trades...")
    if not export_structured_trades():
        success = False
    
    print("\n3. Exporting commentaries...")
    if not export_commentaries():
        success = False
    
    print("\n4. Exporting processing logs...")
    if not export_processing_logs():
        success = False
    
    if success:
        print("\n✅ All exports completed successfully!")
        print("\nGenerated files:")
        print("- raw_trade_history_*.csv (Raw trade data from DTCC API)")
        print("- structured_trade_history_*.csv (Analyzed trade structures)")
        print("- commentary_history_*.csv (Generated market commentaries)")
        print("- processing_logs_*.csv (System processing logs)")
    else:
        print("\n❌ Some exports failed. Check the messages above.")

if __name__ == "__main__":
    main()
