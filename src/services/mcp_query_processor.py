"""
MCP Query Processor for DTCC Trade Analysis
Converts natural language queries into database queries and returns structured results
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, desc, and_, or_
from flask import current_app
from src.models.trade_data import TradeRecord, db

logger = logging.getLogger(__name__)

class MCPQueryProcessor:
    """Processes natural language queries and converts them to database queries"""
    
    def __init__(self):
        self.currency_patterns = {
            'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD',
            'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
            'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP',
            'jpy': 'JPY', 'yen': 'JPY', 'yens': 'JPY',
            'inr': 'INR', 'rupee': 'INR', 'rupees': 'INR',
            'sgd': 'SGD', 'singapore': 'SGD',
            'aud': 'AUD', 'australian': 'AUD',
            'thb': 'THB', 'thai': 'THB', 'baht': 'THB',
            'twd': 'TWD', 'taiwan': 'TWD',
            'krw': 'KRW', 'korean': 'KRW', 'won': 'KRW',
            'hkd': 'HKD', 'hong kong': 'HKD'
        }
        
        self.structure_patterns = {
            'outright': 'Outright',
            'spread': 'Spread',
            'butterfly': 'Butterfly',
            'spreads': 'Spread',
            'butterflies': 'Butterfly'
        }
        
        self.time_patterns = {
            'today': 0,
            'yesterday': 1,
            'last week': 7,
            'last 7 days': 7,
            'last month': 30,
            'last 30 days': 30,
            'this week': 0,
            'this month': 0
        }

    def process_query(self, query: str) -> List[Dict[str, Any]]:
        """Process a natural language query using LLM-first approach"""
        try:
            # Always use LLM to understand the query intent and generate appropriate response
            # This is the core of MCP - let the LLM understand what the user wants
            return self._generate_intelligent_response(query)
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            raise

    def _generate_intelligent_response(self, query: str) -> List[Dict[str, Any]]:
        """Use LLM to understand query intent and generate appropriate response"""
        try:
            # First, get relevant data from database based on query
            params = self._parse_query(query)
            trades = self._execute_query(params)
            
            if not trades:
                return [{"type": "analysis", "content": "No trades found matching your criteria"}]
            
            # Convert to format for LLM analysis
            trade_data = self._format_results(trades, params)
            
            # Use LLM to analyze and respond intelligently
            from src.services.llm_analyzer import LLMAnalyzer, FallbackAnalyzer
            
            llm_analyzer = LLMAnalyzer()
            if llm_analyzer.is_available():
                # Use LLM for intelligent analysis
                analysis = llm_analyzer.analyze_trades(trade_data, query)
                
                # Check if LLM returned an error
                if "not installed" in analysis or "not available" in analysis:
                    # Fallback to structured analysis
                    fallback_analyzer = FallbackAnalyzer()
                    analysis = fallback_analyzer.analyze_trades(trade_data, query)
            else:
                # Use fallback analyzer
                fallback_analyzer = FallbackAnalyzer()
                analysis = fallback_analyzer.analyze_trades(trade_data, query)
            
            return [{
                "type": "analysis",
                "content": analysis,
                "query": query,
                "trade_count": len(trade_data),
                "generated_at": datetime.now().isoformat()
            }]
            
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            return [{"type": "analysis", "content": f"Error processing query: {str(e)}"}]

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query to extract parameters"""
        params = {
            'currencies': [],
            'structures': [],
            'date_range': None,
            'min_dv01': None,
            'max_dv01': None,
            'tenors': [],
            'sort_by': 'created_at',
            'sort_order': 'desc',
            'limit': 1000
        }
        
        # Extract currencies
        for pattern, currency in self.currency_patterns.items():
            if pattern in query:
                params['currencies'].append(currency)
        
        # Extract structures
        for pattern, structure in self.structure_patterns.items():
            if pattern in query:
                params['structures'].append(structure)
        
        # Extract date ranges
        for pattern, days in self.time_patterns.items():
            if pattern in query:
                if days == 0:  # today
                    params['date_range'] = {
                        'start': datetime.now().date(),
                        'end': datetime.now().date()
                    }
                else:
                    params['date_range'] = {
                        'start': (datetime.now() - timedelta(days=days)).date(),
                        'end': datetime.now().date()
                    }
                break
        
        # Extract DV01 ranges
        dv01_match = re.search(r'dv01\s*[><=]+\s*(\d+(?:\.\d+)?)\s*k?', query)
        if dv01_match:
            value = float(dv01_match.group(1))
            if '>' in query:
                params['min_dv01'] = value * 1000  # Convert k to actual value
            elif '<' in query:
                params['max_dv01'] = value * 1000
        
        # Extract tenors
        tenor_match = re.search(r'(\d+)[ym]', query)
        if tenor_match:
            tenor = tenor_match.group(0)
            params['tenors'].append(tenor)
        
        # Extract sorting preferences
        if 'top' in query or 'highest' in query:
            params['sort_order'] = 'desc'
        elif 'lowest' in query:
            params['sort_order'] = 'asc'
        
        # Extract limit
        limit_match = re.search(r'top\s+(\d+)', query)
        if limit_match:
            params['limit'] = int(limit_match.group(1))
        
        return params

    def _execute_query(self, params: Dict[str, Any]) -> List[TradeRecord]:
        """Execute database query based on parsed parameters"""
        # Ensure we're in a Flask app context
        if not current_app:
            from src.main import app
            with app.app_context():
                return self._execute_query_in_context(params)
        else:
            return self._execute_query_in_context(params)
    
    def _execute_query_in_context(self, params: Dict[str, Any]) -> List[TradeRecord]:
        """Execute database query within Flask app context"""
        query = TradeRecord.query
        
        # Filter by currencies
        if params['currencies']:
            query = query.filter(TradeRecord.currency.in_(params['currencies']))
        
        # Filter by structures
        if params['structures']:
            query = query.filter(TradeRecord.structure.in_(params['structures']))
        
        # Filter by date range
        if params['date_range']:
            from datetime import datetime
            start_datetime = datetime.combine(params['date_range']['start'], datetime.min.time())
            end_datetime = datetime.combine(params['date_range']['end'], datetime.max.time())
            query = query.filter(
                and_(
                    TradeRecord.created_at >= start_datetime,
                    TradeRecord.created_at <= end_datetime
                )
            )
        
        # Filter by DV01 range
        if params['min_dv01']:
            query = query.filter(TradeRecord.dv01 >= params['min_dv01'])
        if params['max_dv01']:
            query = query.filter(TradeRecord.dv01 <= params['max_dv01'])
        
        # Always filter for trades with valid DV01 values
        query = query.filter(
            TradeRecord.dv01.isnot(None),
            TradeRecord.dv01 > 0
        )
        
        # Filter by tenors
        if params['tenors']:
            tenor_conditions = []
            for tenor in params['tenors']:
                tenor_conditions.append(TradeRecord.tenor == float(tenor.replace('Y', '').replace('M', '')))
            query = query.filter(or_(*tenor_conditions))
        
        # Apply sorting
        if params['sort_by'] == 'created_at':
            if params['sort_order'] == 'desc':
                query = query.order_by(desc(TradeRecord.created_at))
            else:
                query = query.order_by(TradeRecord.created_at)
        
        # Apply limit
        query = query.limit(params['limit'])
        
        return query.all()

    def _format_results(self, results: List[TradeRecord], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format query results for display"""
        if not results:
            return []
        
        formatted = []
        for record in results:
            # Get DV01 value
            dv01_value = record.dv01 or 0
            
            # Get tenor
            tenor = record.tenor or 0
            
            formatted_record = {
                'id': record.id,
                'currency': record.currency,
                'tenor': tenor,
                'dv01': dv01_value,
                'rates': record.rates,
                'notionals': record.notionals,
                'effective_date': record.effective_date.isoformat() if record.effective_date else None,
                'expiration_date': record.expiration_date.isoformat() if record.expiration_date else None,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'dissemination_identifier': record.dissemination_identifier,
                'upi_underlier_name': record.upi_underlier_name,
                'asset_class': record.asset_class
            }
            
            formatted.append(formatted_record)
        
        return formatted

    def _generate_summary(self, query: str) -> List[Dict[str, Any]]:
        """Generate summary using hybrid approach"""
        try:
            # Parse query to get parameters
            params = self._parse_query(query)
            
            # Get trades from database
            trades = self._execute_query(params)
            
            if not trades:
                return [{"type": "summary", "content": "No trades found matching your criteria"}]
            
            # Convert to format for analysis
            trade_data = self._format_results(trades, params)
            
            # Try LLM analysis first, fallback to structured analysis
            from src.services.llm_analyzer import LLMAnalyzer, FallbackAnalyzer
            
            llm_analyzer = LLMAnalyzer()
            fallback_analyzer = FallbackAnalyzer()
            
            if llm_analyzer.is_available():
                analysis = llm_analyzer.analyze_trades(trade_data, query)
                # Check if LLM returned an error message
                if "not installed" in analysis or "Error calling" in analysis:
                    analysis = fallback_analyzer.generate_summary(trade_data, query)
            else:
                analysis = fallback_analyzer.generate_summary(trade_data, query)
            
            return [{
                "type": "summary",
                "content": analysis,
                "trade_count": len(trades),
                "generated_at": datetime.now().isoformat()
            }]
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return [{"type": "summary", "content": f"Error generating summary: {str(e)}"}]

    def _generate_commentary(self, query: str) -> List[Dict[str, Any]]:
        """Generate commentary using hybrid approach"""
        try:
            # Parse query to get parameters
            params = self._parse_query(query)
            
            # Get trades from database
            trades = self._execute_query(params)
            
            if not trades:
                return [{"type": "commentary", "content": "No trades found matching your criteria"}]
            
            # Convert to format for analysis
            trade_data = self._format_results(trades, params)
            
            # Try LLM analysis first, fallback to structured analysis
            from src.services.llm_analyzer import LLMAnalyzer, FallbackAnalyzer
            
            llm_analyzer = LLMAnalyzer()
            fallback_analyzer = FallbackAnalyzer()
            
            if llm_analyzer.is_available():
                analysis = llm_analyzer.analyze_trades(trade_data, query)
                # Check if LLM returned an error message
                if "not installed" in analysis or "Error calling" in analysis:
                    analysis = fallback_analyzer.analyze_trades(trade_data, query)
            else:
                analysis = fallback_analyzer.analyze_trades(trade_data, query)
            
            return [{
                "type": "commentary",
                "content": analysis,
                "trade_count": len(trades),
                "generated_at": datetime.now().isoformat()
            }]
            
        except Exception as e:
            logger.error(f"Error generating commentary: {e}")
            return [{"type": "commentary", "content": f"Error generating commentary: {str(e)}"}]

    def get_currency_summary(self, currency: str) -> Dict[str, Any]:
        """Get summary statistics for a specific currency"""
        try:
            # Ensure we're in a Flask app context
            if not current_app:
                from src.main import app
                with app.app_context():
                    return self._get_currency_summary_in_context(currency)
            else:
                return self._get_currency_summary_in_context(currency)
        except Exception as e:
            logger.error(f"Error getting currency summary for {currency}: {e}")
            return {'currency': currency, 'error': str(e)}
    
    def _get_currency_summary_in_context(self, currency: str) -> Dict[str, Any]:
        """Get currency summary within Flask app context"""
        try:
            # Only count trades that have DV01 values
            records = TradeRecord.query.filter(
                TradeRecord.currency == currency,
                TradeRecord.dv01.isnot(None),
                TradeRecord.dv01 > 0
            ).all()
            
            if not records:
                return {'currency': currency, 'total_trades': 0, 'total_dv01': 0}
            
            total_dv01 = 0
            asset_classes = {}
            
            for record in records:
                # Sum DV01 (we know it exists and > 0 from the filter)
                total_dv01 += record.dv01
                
                # Count asset classes
                asset_class = record.asset_class or 'Unknown'
                asset_classes[asset_class] = asset_classes.get(asset_class, 0) + 1
            
            return {
                'currency': currency,
                'total_trades': len(records),
                'total_dv01': total_dv01,
                'asset_classes': asset_classes,
                'latest_trade': max(records, key=lambda x: x.created_at or datetime.min).created_at.isoformat() if records else None
            }
        except Exception as e:
            logger.error(f"Error getting currency summary for {currency}: {e}")
            return {'currency': currency, 'error': str(e)}

    def get_top_currencies_by_dv01(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top currencies by total DV01"""
        try:
            # Ensure we're in a Flask app context
            if not current_app:
                from src.main import app
                with app.app_context():
                    return self._get_top_currencies_in_context(limit)
            else:
                return self._get_top_currencies_in_context(limit)
        except Exception as e:
            logger.error(f"Error getting top currencies: {e}")
            return []
    
    def _get_top_currencies_in_context(self, limit: int) -> List[Dict[str, Any]]:
        """Get top currencies within Flask app context"""
        try:
            # This is a simplified version - in production you'd want to use SQL aggregation
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']
            summaries = []
            
            for currency in currencies:
                summary = self._get_currency_summary_in_context(currency)
                if summary.get('total_trades', 0) > 0:
                    summaries.append(summary)
            
            # Sort by total DV01 descending
            summaries.sort(key=lambda x: x.get('total_dv01', 0), reverse=True)
            
            return summaries[:limit]
        except Exception as e:
            logger.error(f"Error getting top currencies in context: {e}")
            return []
