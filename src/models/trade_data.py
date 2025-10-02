from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class TradeRecord(db.Model):
    """Model for storing individual trade records"""
    __tablename__ = 'trade_records'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_time = db.Column(db.DateTime, nullable=False, index=True)
    effective_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=True)
    tenor = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), nullable=False, index=True)
    rates = db.Column(db.Float, nullable=True)
    notionals = db.Column(db.Float, nullable=True)
    dv01 = db.Column(db.Float, nullable=True)
    frequency = db.Column(db.String(50), nullable=True)
    action_type = db.Column(db.String(50), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    asset_class = db.Column(db.String(50), nullable=True)
    upi_underlier_name = db.Column(db.String(200), nullable=True)
    unique_product_identifier = db.Column(db.String(100), nullable=True)
    dissemination_identifier = db.Column(db.String(100), nullable=True)
    other_payment_type = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_time': self.trade_time.isoformat() if self.trade_time else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'tenor': self.tenor,
            'currency': self.currency,
            'rates': self.rates,
            'notionals': self.notionals,
            'dv01': self.dv01,
            'frequency': self.frequency,
            'action_type': self.action_type,
            'event_type': self.event_type,
            'asset_class': self.asset_class,
            'upi_underlier_name': self.upi_underlier_name,
            'unique_product_identifier': self.unique_product_identifier,
            'dissemination_identifier': self.dissemination_identifier,
            'other_payment_type': self.other_payment_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StructuredTrade(db.Model):
    """Model for storing structured trade analysis results"""
    __tablename__ = 'structured_trades'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_time = db.Column(db.DateTime, nullable=False, index=True)
    structure = db.Column(db.String(50), nullable=False, index=True)  # Outright, Spread, Butterfly, Unwind
    start_date = db.Column(db.String(50), nullable=False)  # Effective bucket
    currency = db.Column(db.String(10), nullable=False, index=True)
    tenors = db.Column(db.Text, nullable=False)  # Comma-separated tenors
    rates = db.Column(db.Text, nullable=False)  # Comma-separated rates
    notionals = db.Column(db.Text, nullable=False)  # Comma-separated notionals
    dv01s = db.Column(db.Text, nullable=False)  # Comma-separated DV01s
    package_price = db.Column(db.String(100), nullable=True)
    other_pay_types = db.Column(db.Text, nullable=True)
    metric_bps = db.Column(db.Float, nullable=True)  # Spread/butterfly metric in bps
    expiration = db.Column(db.Date, nullable=True)
    analysis_date = db.Column(db.Date, nullable=False, index=True, default=datetime.utcnow().date())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_time': self.trade_time.isoformat() if self.trade_time else None,
            'structure': self.structure,
            'start_date': self.start_date,
            'currency': self.currency,
            'tenors': self.tenors,
            'rates': self.rates,
            'notionals': self.notionals,
            'dv01s': self.dv01s,
            'package_price': self.package_price,
            'other_pay_types': self.other_pay_types,
            'metric_bps': self.metric_bps,
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Commentary(db.Model):
    """Model for storing generated market commentary"""
    __tablename__ = 'commentaries'
    
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), nullable=False, index=True)
    commentary_text = db.Column(db.Text, nullable=False)
    analysis_date = db.Column(db.Date, nullable=False, index=True, default=datetime.utcnow().date())
    trade_count = db.Column(db.Integer, nullable=False, default=0)
    total_dv01 = db.Column(db.Float, nullable=False, default=0.0)
    structures_summary = db.Column(db.Text, nullable=True)  # JSON string of structure counts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'currency': self.currency,
            'commentary_text': self.commentary_text,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'trade_count': self.trade_count,
            'total_dv01': self.total_dv01,
            'structures_summary': json.loads(self.structures_summary) if self.structures_summary else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProcessingLog(db.Model):
    """Model for tracking processing runs and status"""
    __tablename__ = 'processing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    process_type = db.Column(db.String(50), nullable=False)  # 'parser' or 'analysis'
    status = db.Column(db.String(20), nullable=False)  # 'success', 'error', 'running'
    records_processed = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    execution_time_seconds = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_timestamp': self.run_timestamp.isoformat() if self.run_timestamp else None,
            'process_type': self.process_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'error_message': self.error_message,
            'execution_time_seconds': self.execution_time_seconds
        }

