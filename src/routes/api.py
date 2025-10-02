from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from src.models.trade_data import db, Commentary, StructuredTrade, ProcessingLog
from src.services.data_processor_real import DataProcessor
import json

api_bp = Blueprint('api', __name__)

# Global data processor instance
data_processor = None

def init_data_processor(app):
    """Initialize the data processor with Flask app"""
    global data_processor
    data_processor = DataProcessor(app)
    data_processor.start_background_processing()

@api_bp.route('/commentary', methods=['GET'])
def get_commentary():
    """Get commentary data with currency and date filtering"""
    try:
        # Get query parameters
        currencies = request.args.getlist('currencies')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Default values
        if not currencies:
            currencies = ['USD', 'EUR', 'GBP', 'JPY']
        
        if not start_date:
            start_date = (date.today() - timedelta(days=7)).isoformat()
        
        if not end_date:
            end_date = date.today().isoformat()
        
        # Validate date format
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get commentary data
        commentaries = Commentary.query.filter(
            Commentary.currency.in_(currencies),
            Commentary.analysis_date >= start_dt,
            Commentary.analysis_date <= end_dt
        ).order_by(Commentary.analysis_date.desc(), Commentary.currency).all()
        
        # Group by date
        result = {}
        for commentary in commentaries:
            date_str = commentary.analysis_date.isoformat()
            if date_str not in result:
                result[date_str] = {}
            result[date_str][commentary.currency] = commentary.to_dict()
        
        return jsonify({
            'success': True,
            'data': result,
            'filters': {
                'currencies': currencies,
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/currencies', methods=['GET'])
def get_available_currencies():
    """Get list of available currencies"""
    try:
        currencies = db.session.query(Commentary.currency).distinct().all()
        currency_list = [c[0] for c in currencies]
        
        if not currency_list:
            currency_list = ['USD', 'EUR', 'GBP', 'JPY']  # Default currencies
        
        return jsonify({
            'success': True,
            'currencies': sorted(currency_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/date-range', methods=['GET'])
def get_available_date_range():
    """Get available date range for commentary data"""
    try:
        min_date = db.session.query(db.func.min(Commentary.analysis_date)).scalar()
        max_date = db.session.query(db.func.max(Commentary.analysis_date)).scalar()
        
        if not min_date:
            min_date = date.today()
        if not max_date:
            max_date = date.today()
        
        return jsonify({
            'success': True,
            'min_date': min_date.isoformat(),
            'max_date': max_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/status', methods=['GET'])
def get_processing_status():
    """Get current processing status"""
    try:
        global data_processor
        if not data_processor:
            return jsonify({'error': 'Data processor not initialized'}), 500
        
        status = data_processor.get_processing_status()
        
        # Add summary statistics
        today = date.today()
        today_trades = StructuredTrade.query.filter(
            StructuredTrade.analysis_date == today
        ).count()
        
        today_commentaries = Commentary.query.filter(
            Commentary.analysis_date == today
        ).count()
        
        total_trades = StructuredTrade.query.count()
        total_commentaries = Commentary.query.count()
        
        status.update({
            'today_trades': today_trades,
            'today_commentaries': today_commentaries,
            'total_trades': total_trades,
            'total_commentaries': total_commentaries
        })
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/manual-run', methods=['POST'])
def manual_run():
    """Manually trigger data collection and analysis"""
    try:
        global data_processor
        if not data_processor:
            return jsonify({'error': 'Data processor not initialized'}), 500
        
        run_type = request.json.get('type', 'both')  # 'parser', 'analysis', or 'both'
        
        if run_type in ['parser', 'both']:
            data_processor.run_data_collection()
        
        if run_type in ['analysis', 'both']:
            data_processor.run_data_analysis()
        
        return jsonify({
            'success': True,
            'message': f'Manual {run_type} run completed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/manual-refresh', methods=['POST'])
def manual_refresh():
    """Force refresh data and reload - same as manual-run but specifically for force refresh button"""
    try:
        global data_processor
        if not data_processor:
            return jsonify({'error': 'Data processor not initialized'}), 500
        
        # Always run both parser and analysis for force refresh
        data_processor.run_data_collection()
        data_processor.run_data_analysis()
        
        return jsonify({
            'success': True,
            'message': 'Force refresh completed - data collection and analysis run'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/structured-trades', methods=['GET'])
def get_structured_trades():
    """Get structured trade data with filtering"""
    try:
        # Get query parameters
        currencies = request.args.getlist('currencies')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        structure = request.args.get('structure')  # Optional structure filter
        
        # Build query
        query = StructuredTrade.query
        
        if currencies:
            query = query.filter(StructuredTrade.currency.in_(currencies))
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(StructuredTrade.analysis_date >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(StructuredTrade.analysis_date <= end_dt)
        
        if structure:
            query = query.filter(StructuredTrade.structure == structure)
        
        trades = query.order_by(StructuredTrade.trade_time.desc()).limit(1000).all()
        
        return jsonify({
            'success': True,
            'data': [trade.to_dict() for trade in trades],
            'count': len(trades)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get summary statistics"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (date.today() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get structured trades in date range
        trades = StructuredTrade.query.filter(
            StructuredTrade.analysis_date >= start_dt,
            StructuredTrade.analysis_date <= end_dt
        ).all()
        
        # Calculate summary statistics
        summary = {
            'total_trades': len(trades),
            'by_currency': {},
            'by_structure': {},
            'by_date': {},
            'total_dv01': 0
        }
        
        for trade in trades:
            # By currency
            currency = trade.currency
            if currency not in summary['by_currency']:
                summary['by_currency'][currency] = 0
            summary['by_currency'][currency] += 1
            
            # By structure
            structure = trade.structure
            if structure not in summary['by_structure']:
                summary['by_structure'][structure] = 0
            summary['by_structure'][structure] += 1
            
            # By date
            date_str = trade.analysis_date.isoformat()
            if date_str not in summary['by_date']:
                summary['by_date'][date_str] = 0
            summary['by_date'][date_str] += 1
            
            # Total DV01 (approximate from first DV01 value)
            try:
                dv01_str = trade.dv01s.split(',')[0] if trade.dv01s else '0'
                dv01_value = float(dv01_str)
                summary['total_dv01'] += dv01_value
            except:
                pass
        
        return jsonify({
            'success': True,
            'summary': summary,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

