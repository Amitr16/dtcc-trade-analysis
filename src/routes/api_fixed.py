from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import os
import sys
import json
import subprocess
import logging
from src.models.trade_data import db, ProcessingLog

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/commentary', methods=['GET'])
def get_commentary():
    """Get market commentary data by reading generated files directly"""
    try:
        # Get query parameters
        currencies = request.args.getlist('currencies')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not currencies:
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
        
        # Read commentary files directly
        commentary_data = {}
        today = date.today().isoformat()
        
        # Get the directory where commentary files are stored
        script_dir = os.path.dirname(os.path.dirname(__file__))
        
        for currency in currencies:
            try:
                commentary_file = os.path.join(script_dir, f'{currency.lower()}_commentary.txt')
                
                if os.path.exists(commentary_file):
                    with open(commentary_file, 'r', encoding='utf-8') as f:
                        commentary_text = f.read().strip()
                    
                    if commentary_text:
                        if today not in commentary_data:
                            commentary_data[today] = {}
                        
                        # Count trades and calculate DV01 from commentary
                        trade_count = commentary_text.count('traded')
                        total_dv01 = 0
                        
                        # Extract DV01 values from commentary
                        import re
                        dv01_matches = re.findall(r'(\d+(?:\.\d+)?[kM]?)\s+DV01', commentary_text)
                        for match in dv01_matches:
                            try:
                                if 'k' in match:
                                    total_dv01 += float(match.replace('k', '')) * 1000
                                elif 'M' in match:
                                    total_dv01 += float(match.replace('M', '')) * 1000000
                                else:
                                    total_dv01 += float(match)
                            except:
                                continue
                        
                        commentary_data[today][currency] = {
                            'commentary_text': commentary_text,
                            'trade_count': trade_count,
                            'total_dv01': total_dv01
                        }
                        
            except Exception as e:
                logger.warning(f"Error reading commentary for {currency}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'data': commentary_data
        })
        
    except Exception as e:
        logger.error(f"Error getting commentary: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get summary statistics"""
    try:
        # Calculate summary from commentary files
        script_dir = os.path.dirname(os.path.dirname(__file__))
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
        
        total_trades = 0
        total_dv01 = 0
        active_currencies = 0
        by_currency = {}
        
        for currency in currencies:
            try:
                commentary_file = os.path.join(script_dir, f'{currency.lower()}_commentary.txt')
                
                if os.path.exists(commentary_file):
                    with open(commentary_file, 'r', encoding='utf-8') as f:
                        commentary_text = f.read().strip()
                    
                    if commentary_text and 'traded' in commentary_text:
                        active_currencies += 1
                        
                        # Count trades
                        trade_count = commentary_text.count('traded')
                        total_trades += trade_count
                        
                        # Extract DV01
                        import re
                        currency_dv01 = 0
                        dv01_matches = re.findall(r'(\d+(?:\.\d+)?[kM]?)\s+DV01', commentary_text)
                        for match in dv01_matches:
                            try:
                                if 'k' in match:
                                    currency_dv01 += float(match.replace('k', '')) * 1000
                                elif 'M' in match:
                                    currency_dv01 += float(match.replace('M', '')) * 1000000
                                else:
                                    currency_dv01 += float(match)
                            except:
                                continue
                        
                        total_dv01 += currency_dv01
                        by_currency[currency] = {
                            'trade_count': trade_count,
                            'total_dv01': currency_dv01
                        }
                        
            except Exception as e:
                logger.warning(f"Error processing summary for {currency}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'summary': {
                'total_trades': total_trades,
                'total_dv01': total_dv01,
                'active_currencies': active_currencies,
                'by_currency': by_currency
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/currencies', methods=['GET'])
def get_currencies():
    """Get available currencies"""
    try:
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
        return jsonify({
            'success': True,
            'currencies': currencies
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/date-range', methods=['GET'])
def get_available_date_range():
    """Get available date range"""
    try:
        today = date.today()
        return jsonify({
            'success': True,
            'min_date': today.isoformat(),
            'max_date': today.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get processing status including real scheduler status"""
    try:
        from src.services.simple_scheduler import get_scheduler
        
        # Get scheduler status
        scheduler = get_scheduler()
        status_data = scheduler.get_status()
        
        # Get processing logs from database
        recent_logs = []
        try:
            db_logs = ProcessingLog.query.order_by(ProcessingLog.run_timestamp.desc()).limit(10).all()
            for log in db_logs:
                recent_logs.append({
                    'process_type': log.process_type.upper(),
                    'status': log.status,
                    'run_timestamp': log.run_timestamp.isoformat() if log.run_timestamp else None,
                    'records_processed': f"{log.records_processed} records" if log.records_processed else 'N/A',
                    'execution_time_seconds': round(log.execution_time_seconds, 2) if log.execution_time_seconds else 0,
                    'error_message': log.error_message
                })
        except Exception as e:
            logger.error(f"Error fetching processing logs: {e}")
            # Fallback to scheduler status
            if status_data.get('last_run'):
                recent_logs.append({
                    'process_type': 'AUTOMATIC',
                    'status': 'success' if 'completed' in status_data.get('status', '') else 'running',
                    'run_timestamp': status_data['last_run'],
                    'records_processed': 'Scripts executed successfully',
                    'execution_time_seconds': 0.1,
                    'error_message': status_data.get('error')
                })
        
        return jsonify({
            'success': True,
            'status': {
                'running': status_data.get('running', False),
                'scheduler_active': status_data.get('running', False),
                'recent_logs': recent_logs,
                'automation_status': f"🔄 ACTIVE - Last run: {status_data.get('timestamp', 'Never')}" if status_data.get('running') else '❌ INACTIVE',
                'raw_status': status_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/manual-run', methods=['POST'])
def manual_run():
    """Manually trigger data analysis only"""
    try:
        # Run DTCCAnalysis.py directly
        script_dir = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(script_dir, 'DTCCAnalysis.py')
        
        if os.path.exists(script_path):
            result = subprocess.run([
                sys.executable, script_path
            ], cwd=script_dir, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': 'Manual analysis completed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.stderr
                })
        else:
            return jsonify({
                'success': False,
                'error': 'DTCCAnalysis.py not found'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/manual-refresh', methods=['POST'])
def manual_refresh():
    """Force refresh - run both parser and analysis"""
    try:
        from src.services.simple_scheduler import get_scheduler
        
        # Use scheduler for manual execution
        scheduler = get_scheduler()
        success = scheduler.run_manual()
        
        if success:
            return jsonify({
                'success': True,
                'message': '🔄 Force refresh completed - both data collection and analysis run successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Force refresh failed - check logs'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/mcp-query', methods=['POST'])
def mcp_query():
    """Process natural language queries using MCP-like functionality"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        # Process the query using the MCP query processor
        from src.services.mcp_query_processor import MCPQueryProcessor
        processor = MCPQueryProcessor()
        
        results = processor.process_query(query)
        
        # Get background processing status
        processing_status = get_background_processing_status()
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'processing_status': processing_status
        })
        
    except Exception as e:
        logger.error(f"Error processing MCP query: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_background_processing_status():
    """Get current background processing status"""
    try:
        from flask import current_app
        from datetime import datetime
        
        # Get recent processing logs
        recent_logs = ProcessingLog.query.order_by(ProcessingLog.run_timestamp.desc()).limit(3).all()
        
        status_messages = []
        
        # Check if analysis is currently running
        if recent_logs and recent_logs[0].process_type == 'analysis' and recent_logs[0].status == 'running':
            status_messages.append("🔄 Running data analysis...")
        elif recent_logs and recent_logs[0].process_type == 'parser' and recent_logs[0].status == 'running':
            status_messages.append("📊 Fetching new trade data...")
        
        # Check for recent commentary generation
        if recent_logs:
            for log in recent_logs:
                if log.process_type == 'analysis' and log.status == 'success':
                    status_messages.append(f"✅ Analysis completed: {log.records_processed} trades processed")
                    break
        
        # Check if scheduler is active by looking at recent logs
        if recent_logs:
            # If we have recent successful analysis logs, scheduler is likely active
            recent_analysis = [log for log in recent_logs if log.process_type == 'analysis' and log.status == 'success']
            if recent_analysis:
                last_analysis = recent_analysis[0]
                time_diff = (datetime.utcnow() - last_analysis.run_timestamp).total_seconds()
                if time_diff < 120:  # Within last 2 minutes
                    status_messages.append("⏰ Background scheduler active - updating every 60 seconds")
        
        return {
            'active': len(status_messages) > 0,
            'messages': status_messages[:3],  # Limit to 3 messages
            'last_update': recent_logs[0].run_timestamp.isoformat() if recent_logs else None
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        return {
            'active': False,
            'messages': [],
            'last_update': None
        }

def init_data_processor(app=None):
    """Initialize the data processor"""
    try:
        from src.services.data_processor import DataProcessor
        processor = DataProcessor(app)
        processor.start_background_processing()
        logger.info("Data processor initialized and started")
        return processor
    except Exception as e:
        logger.error(f"Error initializing data processor: {e}")
        return None

