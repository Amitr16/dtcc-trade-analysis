import os
import sys
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import threading
import time
import traceback
import subprocess
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None
        
    def start_background_processing(self):
        """Start the background processing thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._background_loop, daemon=True)
            self.thread.start()
            logger.info("Background processing started")
    
    def stop_background_processing(self):
        """Stop the background processing thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Background processing stopped")
    
    def _background_loop(self):
        """Main background processing loop - runs every minute"""
        while self.running:
            try:
                with self.app.app_context():
                    # Run data collection and analysis
                    self.run_data_collection()
                    self.run_data_analysis()
                    
                # Sleep for 60 seconds (1 minute)
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                time.sleep(60)  # Continue after error
    
    def run_data_collection(self):
        """Run DTCC data collection using DTCCParser.py"""
        from src.models.trade_data import db, ProcessingLog, TradeRecord
        
        start_time = time.time()
        log_entry = ProcessingLog(
            process_type='collection',
            status='running',
            records_processed=0
        )
        
        try:
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info("Starting DTCC data collection...")
            
            # Run DTCCParser.py script
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DTCCParser.py')
            
            if os.path.exists(script_path):
                try:
                    # Run the DTCC parser script
                    result = subprocess.run([
                        'python3', script_path
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        logger.info("DTCC Parser completed successfully")
                        
                        # Load the generated trade_data.csv and store in database
                        trade_data_path = os.path.join(os.path.dirname(script_path), 'trade_data.csv')
                        records_added = self._load_trade_data_to_db(trade_data_path)
                        
                        log_entry.status = 'success'
                        log_entry.records_processed = records_added
                        
                    else:
                        logger.error(f"DTCC Parser failed: {result.stderr}")
                        log_entry.status = 'error'
                        log_entry.error_message = result.stderr
                        
                except subprocess.TimeoutExpired:
                    logger.error("DTCC Parser timed out")
                    log_entry.status = 'error'
                    log_entry.error_message = "Process timed out"
                    
                except Exception as e:
                    logger.error(f"Error running DTCC Parser: {e}")
                    log_entry.status = 'error'
                    log_entry.error_message = str(e)
            else:
                logger.warning("DTCCParser.py not found, skipping data collection")
                log_entry.status = 'success'
                log_entry.records_processed = 0
            
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
            
            logger.info("Data collection completed")
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
    
    def _load_trade_data_to_db(self, csv_path):
        """Load trade data from CSV to database"""
        from src.models.trade_data import db, TradeRecord
        import pandas as pd
        
        if not os.path.exists(csv_path):
            return 0
        
        try:
            # Read CSV with minimal pandas usage
            import csv
            records_added = 0
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Check if record already exists
                        existing = TradeRecord.query.filter_by(
                            dissemination_identifier=row.get('Dissemination Identifier', '')
                        ).first()
                        
                        if not existing:
                            trade_record = TradeRecord(
                                trade_time=datetime.fromisoformat(row.get('Trade Time', '').replace('Z', '+00:00')) if row.get('Trade Time') else datetime.now(),
                                effective_date=datetime.fromisoformat(row.get('Effective Date', '').replace('Z', '+00:00')).date() if row.get('Effective Date') else date.today(),
                                expiration_date=datetime.fromisoformat(row.get('Expiration Date', '').replace('Z', '+00:00')).date() if row.get('Expiration Date') else None,
                                tenor=row.get('Tenor', ''),
                                currency=row.get('Currency', ''),
                                rates=float(row.get('Rates', 0)) if row.get('Rates') else 0.0,
                                notionals=float(row.get('Notionals', 0)) if row.get('Notionals') else 0.0,
                                dv01=float(row.get('Dv01', 0)) if row.get('Dv01') else 0.0,
                                frequency=row.get('Frequency', ''),
                                action_type=row.get('Action Type', ''),
                                event_type=row.get('Event Type', ''),
                                asset_class=row.get('Asset Class', ''),
                                upi_underlier_name=row.get('UPI Underlier Name', ''),
                                unique_product_identifier=row.get('Unique Product Identifier', ''),
                                dissemination_identifier=row.get('Dissemination Identifier', ''),
                                other_payment_type=row.get('Other Payment Type', '')
                            )
                            db.session.add(trade_record)
                            records_added += 1
                    except Exception as e:
                        logger.warning(f"Error processing trade record: {e}")
                        continue
            
            db.session.commit()
            return records_added
            
        except Exception as e:
            logger.error(f"Error loading trade data to database: {e}")
            return 0
    
    def run_data_analysis(self):
        """Run DTCC data analysis using DTCCAnalysis.py"""
        from src.models.trade_data import db, ProcessingLog, Commentary, StructuredTrade
        
        start_time = time.time()
        log_entry = ProcessingLog(
            process_type='analysis',
            status='running',
            records_processed=0
        )
        
        try:
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info("Starting DTCC data analysis...")
            
            # Create temporary trade_data.csv from database
            temp_csv_path = self._export_trade_data_to_csv()
            
            if temp_csv_path and os.path.exists(temp_csv_path):
                # Run DTCCAnalysis.py script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DTCCAnalysis.py')
                
                if os.path.exists(script_path):
                    try:
                        # Change to the script directory and run analysis
                        script_dir = os.path.dirname(script_path)
                        
                        # Copy temp CSV to script directory as trade_data.csv
                        import shutil
                        target_csv = os.path.join(script_dir, 'trade_data.csv')
                        shutil.copy2(temp_csv_path, target_csv)
                        
                        # Run the analysis script
                        result = subprocess.run([
                            'python3', script_path
                        ], cwd=script_dir, capture_output=True, text=True, timeout=300)
                        
                        if result.returncode == 0:
                            logger.info("DTCC Analysis completed successfully")
                            
                            # Load the generated commentary files
                            records_added = self._load_commentary_to_db(script_dir)
                            
                            log_entry.status = 'success'
                            log_entry.records_processed = records_added
                            
                        else:
                            logger.error(f"DTCC Analysis failed: {result.stderr}")
                            log_entry.status = 'error'
                            log_entry.error_message = result.stderr
                            
                    except subprocess.TimeoutExpired:
                        logger.error("DTCC Analysis timed out")
                        log_entry.status = 'error'
                        log_entry.error_message = "Process timed out"
                        
                    except Exception as e:
                        logger.error(f"Error running DTCC Analysis: {e}")
                        log_entry.status = 'error'
                        log_entry.error_message = str(e)
                else:
                    logger.warning("DTCCAnalysis.py not found")
                    log_entry.status = 'error'
                    log_entry.error_message = "DTCCAnalysis.py not found"
            else:
                logger.warning("No trade data available for analysis")
                log_entry.status = 'success'
                log_entry.records_processed = 0
            
            # Clean up temp file
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
            
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
            
            logger.info("Data analysis completed")
            
        except Exception as e:
            logger.error(f"Error in data analysis: {e}")
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
    
    def _export_trade_data_to_csv(self):
        """Export trade data from database to CSV for analysis"""
        from src.models.trade_data import TradeRecord
        
        try:
            # Get recent trade data (last 30 days)
            cutoff_date = date.today() - timedelta(days=30)
            trade_records = TradeRecord.query.filter(
                TradeRecord.effective_date >= cutoff_date
            ).all()
            
            if not trade_records:
                return None
            
            # Create temporary CSV file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            
            # Write CSV header
            temp_file.write('Trade Time,Effective Date,Expiration Date,Tenor,Currency,Rates,Notionals,Dv01,Frequency,Action Type,Event Type,Asset Class,UPI Underlier Name,Unique Product Identifier,Dissemination Identifier,Other Payment Type\n')
            
            # Write trade data
            for record in trade_records:
                temp_file.write(f'{record.trade_time},{record.effective_date},{record.expiration_date or ""},{record.tenor},{record.currency},{record.rates},{record.notionals},{record.dv01},{record.frequency},{record.action_type},{record.event_type},{record.asset_class},{record.upi_underlier_name},{record.unique_product_identifier},{record.dissemination_identifier},{record.other_payment_type}\n')
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error exporting trade data to CSV: {e}")
            return None
    
    def _load_commentary_to_db(self, script_dir):
        """Load generated commentary files to database"""
        from src.models.trade_data import db, Commentary
        
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
        today = date.today()
        records_added = 0
        
        for currency in currencies:
            try:
                commentary_file = os.path.join(script_dir, f'{currency.lower()}_commentary.txt')
                
                if os.path.exists(commentary_file):
                    with open(commentary_file, 'r') as f:
                        commentary_text = f.read().strip()
                    
                    # Clear existing commentary for today and currency
                    Commentary.query.filter(
                        Commentary.analysis_date == today,
                        Commentary.currency == currency
                    ).delete()
                    
                    # Create new commentary record
                    commentary_record = Commentary(
                        currency=currency,
                        commentary_text=commentary_text,
                        analysis_date=today,
                        trade_count=0,  # Will be updated by analysis
                        total_dv01=0.0,  # Will be updated by analysis
                        structures_summary=json.dumps({})
                    )
                    db.session.add(commentary_record)
                    records_added += 1
                    
            except Exception as e:
                logger.warning(f"Error loading commentary for {currency}: {e}")
                continue
        
        db.session.commit()
        return records_added
    
    def get_processing_status(self):
        """Get current processing status"""
        from src.models.trade_data import ProcessingLog
        
        try:
            recent_logs = ProcessingLog.query.order_by(
                ProcessingLog.run_timestamp.desc()
            ).limit(10).all()
            
            logs_data = []
            for log in recent_logs:
                logs_data.append({
                    'process_type': log.process_type,
                    'status': log.status,
                    'run_timestamp': log.run_timestamp.isoformat(),
                    'records_processed': log.records_processed,
                    'execution_time_seconds': log.execution_time_seconds,
                    'error_message': log.error_message
                })
            
            return {
                'running': self.running,
                'recent_logs': logs_data
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {
                'running': self.running,
                'recent_logs': [],
                'error': str(e)
            }

