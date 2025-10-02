import os
import sys
import pandas as pd
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import threading
import time
import traceback

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.trade_data import db, TradeRecord, StructuredTrade, Commentary, ProcessingLog
from src.DTCCParser import fetch_trade_data, process_trades, get_existing_trade_timestamps
from src.DTCCAnalysis import DTCCAnalysis

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
                
                # Wait for 60 seconds (1 minute)
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                logger.error(traceback.format_exc())
                time.sleep(60)  # Wait before retrying
    
    def run_data_collection(self):
        """Run DTCC data collection and store in database"""
        start_time = time.time()
        log_entry = ProcessingLog(
            process_type='parser',
            status='running',
            records_processed=0
        )
        
        try:
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info("Starting DTCC data collection...")
            
            # Fetch data from DTCC API
            json_data = fetch_trade_data()
            if not json_data or 'tradeList' not in json_data:
                raise Exception("No trade data fetched or 'tradeList' not found in response")
            
            trades = json_data['tradeList']
            processed_trades = process_trades(trades)
            
            if not processed_trades:
                logger.info("No new trades to process")
                log_entry.status = 'success'
                log_entry.records_processed = 0
                log_entry.execution_time_seconds = time.time() - start_time
                db.session.commit()
                return
            
            # Get existing dissemination identifiers to avoid duplicates
            existing_dissemination_ids = self._get_existing_dissemination_ids_from_db()
            
            # Process trades and handle corrections
            new_trades = []
            trades_to_delete = []
            
            for trade in processed_trades:
                dissemination_id = trade.get('Dissemination Identifier', '')
                original_dissemination_id = trade.get('Original Dissemination Identifier', '')
                
                if not dissemination_id:
                    continue
                
                # Check if this is a correction (has originalDisseminationIdentifier)
                if original_dissemination_id:
                    # This is a correction - find and mark original trade for deletion
                    if original_dissemination_id in existing_dissemination_ids:
                        trades_to_delete.append(original_dissemination_id)
                        logger.info(f"Found correction: will replace trade {original_dissemination_id} with {dissemination_id}")
                else:
                    # This is a new trade - check for uniqueness
                    if dissemination_id in existing_dissemination_ids:
                        logger.info(f"Trade {dissemination_id} already exists, skipping")
                        continue
                
                # Add this trade (whether new or correction)
                new_trades.append(trade)
            
            # Delete corrected trades from database
            if trades_to_delete:
                deleted_count = TradeRecord.query.filter(
                    TradeRecord.dissemination_identifier.in_(trades_to_delete)
                ).delete(synchronize_session=False)
                db.session.commit()
                logger.info(f"Deleted {deleted_count} corrected trades from database")
            
            # Store new trades in database
            records_added = 0
            for trade in new_trades:
                try:
                    trade_record = TradeRecord(
                        trade_time=pd.to_datetime(trade.get('Trade Time')),
                        effective_date=pd.to_datetime(trade.get('Effective Date')).date(),
                        expiration_date=pd.to_datetime(trade.get('Expiration Date')).date() if trade.get('Expiration Date') else None,
                        tenor=float(trade.get('Tenor')) if trade.get('Tenor') and trade.get('Tenor') != '' else None,
                        currency=trade.get('Currency', ''),
                        rates=float(trade.get('Rates')) if trade.get('Rates') and trade.get('Rates') != '' else None,
                        notionals=self._clean_numeric_value(trade.get('Notionals')),
                        dv01=float(trade.get('Dv01')) if trade.get('Dv01') and trade.get('Dv01') != '' else None,
                        frequency=trade.get('Frequency', ''),
                        action_type=trade.get('Action Type', ''),
                        event_type=trade.get('Event Type', ''),
                        asset_class=trade.get('Asset Class', ''),
                        upi_underlier_name=trade.get('UPI Underlier Name', ''),
                        unique_product_identifier=trade.get('Unique Product Identifier', ''),
                        dissemination_identifier=trade.get('Dissemination Identifier', ''),
                        other_payment_type=trade.get('Other Payment Type', '')
                    )
                    db.session.add(trade_record)
                    records_added += 1
                except Exception as e:
                    logger.warning(f"Error processing trade record: {e}")
                    continue
            
            db.session.commit()
            
            # Export all trade data to CSV for debugging
            self._export_trade_data_to_csv()
            
            # Update log entry
            log_entry.status = 'success'
            log_entry.records_processed = records_added
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
            
            logger.info(f"Data collection completed: {records_added} new trades added")
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
    
    def run_data_analysis(self):
        """Run DTCC data analysis and store results"""
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
            
            # Get all trade data from database for analysis
            today = date.today()
            trade_records = TradeRecord.query.all()
            
            if not trade_records:
                logger.info("No trades to analyze for today")
                log_entry.status = 'success'
                log_entry.records_processed = 0
                log_entry.execution_time_seconds = time.time() - start_time
                db.session.commit()
                return
            
            # Convert to DataFrame for analysis
            trade_data = []
            for record in trade_records:
                trade_data.append({
                    'Trade Time': record.trade_time,
                    'Effective Date': record.effective_date,
                    'Expiration Date': record.expiration_date,
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
                    'Other Payment Type': record.other_payment_type
                })
            
            # Save to temporary CSV for analysis
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_csv_path = os.path.join(temp_dir, 'dtcc_temp_trade_data.csv')
            
            try:
                df = pd.DataFrame(trade_data)
                df.to_csv(temp_csv_path, index=False)
                logger.info(f"Temporary CSV created at: {temp_csv_path}")
            except Exception as e:
                logger.error(f"Error creating temporary CSV: {e}")
                # Fallback to a different location
                temp_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_trade_data.csv')
                df.to_csv(temp_csv_path, index=False)
                logger.info(f"Fallback CSV created at: {temp_csv_path}")
            
            # Run analysis
            analyzer = DTCCAnalysis(input_file=temp_csv_path)
            analyzer.load_and_prepare_data()
            analyzer.detect_structures()
            
            # Clear existing structured trades for today
            StructuredTrade.query.filter(StructuredTrade.analysis_date == today).delete()
            
            # Store structured trades
            records_added = 0
            for structured_trade in analyzer.structured_output:
                try:
                    trade_record = StructuredTrade(
                        trade_time=pd.to_datetime(structured_trade['Trade Time']),
                        structure=structured_trade['Structure'],
                        start_date=structured_trade['Start Date'],
                        currency=structured_trade['Currency'],
                        tenors=structured_trade['Tenors'],
                        rates=str(structured_trade['Rates']),
                        notionals=str(structured_trade['Notionals']),
                        dv01s=str(structured_trade['DV01s']),
                        package_price=structured_trade.get('Package Price', ''),
                        other_pay_types=structured_trade.get('Other Pay Types', ''),
                        metric_bps=float(structured_trade['Metric (bps)']) if structured_trade['Metric (bps)'] != '' else None,
                        expiration=pd.to_datetime(structured_trade['Expiration']).date() if structured_trade.get('Expiration') else None,
                        analysis_date=today
                    )
                    db.session.add(trade_record)
                    records_added += 1
                except Exception as e:
                    logger.warning(f"Error processing structured trade: {e}")
                    continue
            
            # Generate and store commentary for each currency
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
            for currency in currencies:
                try:
                    commentary_text = analyzer.generate_commentary(currency)
                    
                    # Calculate summary statistics
                    currency_trades = [t for t in analyzer.structured_output if t['Currency'] == currency]
                    trade_count = len(currency_trades)
                    
                    if trade_count > 0:
                        total_dv01 = sum(float(str(t['DV01s']).split(',')[0]) for t in currency_trades if t['DV01s'])
                        structures_summary = {}
                        for trade in currency_trades:
                            structure = trade['Structure']
                            structures_summary[structure] = structures_summary.get(structure, 0) + 1
                        
                        # Clear existing commentary for today and currency
                        Commentary.query.filter(
                            Commentary.analysis_date == today,
                            Commentary.currency == currency
                        ).delete()
                        
                        # Store new commentary
                        commentary_record = Commentary(
                            currency=currency,
                            commentary_text=commentary_text,
                            analysis_date=today,
                            trade_count=trade_count,
                            total_dv01=total_dv01,
                            structures_summary=json.dumps(structures_summary)
                        )
                        db.session.add(commentary_record)
                        
                        # Write commentary file for frontend in the src directory
                        src_dir = os.path.dirname(os.path.dirname(__file__))
                        commentary_file = os.path.join(src_dir, f'{currency.lower()}_commentary.txt')
                        with open(commentary_file, 'w', encoding='utf-8') as f:
                            f.write(commentary_text)
                        logger.info(f"Generated commentary file: {commentary_file}")
                        
                except Exception as e:
                    logger.warning(f"Error generating commentary for {currency}: {e}")
                    # Rollback any partial changes for this currency
                    db.session.rollback()
                    continue
            
            db.session.commit()
            
            # Clean up temp file
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
            
            # Update log entry
            log_entry.status = 'success'
            log_entry.records_processed = records_added
            log_entry.execution_time_seconds = time.time() - start_time
            db.session.commit()
            
            logger.info(f"Data analysis completed: {records_added} structured trades processed")
            
        except Exception as e:
            logger.error(f"Error in data analysis: {e}")
            # Rollback the session to clean state
            db.session.rollback()
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = time.time() - start_time
            try:
                db.session.commit()
            except Exception as commit_error:
                logger.error(f"Error committing log entry: {commit_error}")
                db.session.rollback()
    
    def _get_existing_trade_timestamps_from_db(self):
        """Get existing trade timestamps from database"""
        existing_records = TradeRecord.query.with_entities(TradeRecord.trade_time).all()
        return {record.trade_time.isoformat() for record in existing_records}
    
    def _get_existing_dissemination_ids_from_db(self):
        """Get existing dissemination identifiers from database"""
        existing_records = TradeRecord.query.with_entities(TradeRecord.dissemination_identifier).all()
        return {record.dissemination_identifier for record in existing_records if record.dissemination_identifier}
    
    def _clean_numeric_value(self, value):
        """Clean numeric values for database storage"""
        if pd.isna(value) or value == '' or value is None:
            return None
        
        try:
            str_value = str(value).strip()
            str_value = str_value.replace(',', '')
            str_value = str_value.replace('+', '')
            str_value = str_value.replace('$', '')
            
            if str_value == '' or str_value == 'nan':
                return None
            
            return float(str_value)
        except (ValueError, TypeError):
            return None
    
    def get_commentary_by_filters(self, currencies: List[str], start_date: str, end_date: str) -> Dict:
        """Get commentary data filtered by currencies and date range"""
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            commentaries = Commentary.query.filter(
                Commentary.currency.in_(currencies),
                Commentary.analysis_date >= start_dt,
                Commentary.analysis_date <= end_dt
            ).order_by(Commentary.analysis_date.desc(), Commentary.currency).all()
            
            result = {}
            for commentary in commentaries:
                date_str = commentary.analysis_date.isoformat()
                if date_str not in result:
                    result[date_str] = {}
                result[date_str][commentary.currency] = commentary.to_dict()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting commentary by filters: {e}")
            return {}
    
    def get_processing_status(self) -> Dict:
        """Get current processing status and recent logs"""
        try:
            recent_logs = ProcessingLog.query.order_by(
                ProcessingLog.run_timestamp.desc()
            ).limit(10).all()
            
            return {
                'running': self.running,
                'recent_logs': [log.to_dict() for log in recent_logs]
            }
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {'running': False, 'recent_logs': []}
    
    def _export_trade_data_to_csv(self):
        """Export all trade data from database to CSV for debugging"""
        try:
            # Get all trade records from database
            trade_records = TradeRecord.query.order_by(TradeRecord.trade_time.desc()).all()
            
            if not trade_records:
                logger.info("No trade records to export")
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
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'trade_data.csv')
            df.to_csv(csv_path, index=False)
            
            logger.info(f"Exported {len(trade_records)} trade records to {csv_path}")
            
        except Exception as e:
            logger.error(f"Error exporting trade data to CSV: {e}")

