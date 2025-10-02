#!/usr/bin/env python3
"""
Export database to CSV for analysis
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.trade_data import db, TradeRecord
from flask import Flask
import pandas as pd

def create_app():
    """Create Flask app for database access"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def export_database_to_csv():
    """Export database to CSV"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all trade records from database
            trade_records = TradeRecord.query.order_by(TradeRecord.trade_time.desc()).all()
            
            if not trade_records:
                print("No trade records to export")
                return
            
            # Convert to list of dictionaries
            trade_data = []
            for record in trade_records:
                trade_data.append({
                    'Trade Time': record.trade_time.isoformat() if record.trade_time else '',
                    'Effective Date': record.effective_date.isoformat() if record.effective_date else '',
                    'Expiration Date': record.expiration_date.isoformat() if record.expiration_date else '',
                    'Tenor': record.tenor,
                    'Currency': record.currency,
                    'Rates': record.rates,
                    'Notionals': record.notionals,
                    'Dv01': record.dv01,
                    'Frequency': record.frequency,
                    'Action Type': record.action_type,
                    'Event Type': record.event_type,
                    'Asset Class': record.asset_class,
                    'UPI Underlier Name': record.upi_underlier_name,
                    'Unique Product Identifier': record.unique_product_identifier,
                    'Dissemination Identifier': record.dissemination_identifier,
                    'Other Payment Type': record.other_payment_type,
                    'Created At': record.created_at.isoformat() if record.created_at else ''
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(trade_data)
            csv_path = os.path.join('src', 'trade_data.csv')
            df.to_csv(csv_path, index=False)
            
            print(f"✅ Exported {len(trade_records)} trade records to {csv_path}")
            
        except Exception as e:
            print(f"❌ Error exporting trade data to CSV: {e}")

if __name__ == "__main__":
    print("Exporting database to CSV...")
    export_database_to_csv()
