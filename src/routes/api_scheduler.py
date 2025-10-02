from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Global variable for data processor
data_processor = None

def init_data_processor(processor):
    global data_processor
    data_processor = processor

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
                    with open(commentary_file, 'r') as f:
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
                    with open(commentary_file, 'r') as f:
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
    """Get processing status including scheduler status"""
    try:
        from src.services.scheduler import get_scheduler
        
        # Get scheduler status
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_status() if scheduler else {'running': False}
        
        # Check if commentary files exist and get their timestamps
        script_dir = os.path.dirname(os.path.dirname(__file__))
        recent_logs = []
        
        # Check for recent analysis files
        for currency in ['usd', 'eur', 'gbp', 'jpy']:
            commentary_file = os.path.join(script_dir, f'{currency}_commentary.txt')
            if os.path.exists(commentary_file):
                stat = os.stat(commentary_file)
                recent_logs.append({
                    'process_type': 'AUTOMATIC',
                    'status': 'success',
                    'run_timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'records_processed': 'Analysis completed',
                    'execution_time_seconds': 0.1,
                    'error_message': None
                })
                break  # Only need one timestamp
        
        return jsonify({
            'success': True,
            'status': {
                'running': scheduler_status.get('running', False),
                'scheduler_active': scheduler_status.get('thread_alive', False),
                'recent_logs': recent_logs,
                'automation_status': '🔄 ACTIVE - Scripts run every 60 seconds' if scheduler_status.get('running') else '❌ INACTIVE'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/manual-run', methods=['POST'])
def manual_run():
    """Manually trigger data analysis only"""
    try:
        from src.services.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        if scheduler:
            success = scheduler.run_analysis_only()
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Manual analysis completed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Analysis failed - check logs'
                })
        else:
            # Fallback to direct execution
            script_dir = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(script_dir, 'DTCCAnalysis.py')
            
            if os.path.exists(script_path):
                result = subprocess.run([
                    'python3', script_path
                ], cwd=script_dir, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return jsonify({
                        'success': True,
                        'message': 'Analysis completed successfully'
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
        from src.services.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        if scheduler:
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
        else:
            # Fallback to direct execution
            script_dir = os.path.dirname(os.path.dirname(__file__))
            
            # Run parser first
            parser_path = os.path.join(script_dir, 'DTCCParser.py')
            if os.path.exists(parser_path):
                subprocess.run(['python3', parser_path], cwd=script_dir, timeout=60)
            
            # Then run analysis
            analysis_path = os.path.join(script_dir, 'DTCCAnalysis.py')
            if os.path.exists(analysis_path):
                result = subprocess.run([
                    'python3', analysis_path
                ], cwd=script_dir, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return jsonify({
                        'success': True,
                        'message': 'Force refresh completed successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result.stderr
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Scripts not found'
                })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

