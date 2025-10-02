import logging
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from src.models.trade_data import TradeRecord, db
from src.services.llm_analyzer import LLMAnalyzer, FallbackAnalyzer

logger = logging.getLogger(__name__)

class MCPQueryProcessor:
    """Model Context Protocol Query Processor - LLM-first approach"""
    
    def __init__(self):
        self.llm_analyzer = LLMAnalyzer()
        self.fallback_analyzer = FallbackAnalyzer()

    def process_query(self, query: str) -> List[Dict[str, Any]]:
        """Process a natural language query using LLM-first approach"""
        try:
            # Get today's trades by default, unless user specifies otherwise
            today = date.today()
            
            # Simple keyword detection for date ranges
            query_lower = query.lower()
            if 'yesterday' in query_lower:
                yesterday = today - timedelta(days=1)
                start_date, end_date = yesterday, yesterday
            elif 'last week' in query_lower or 'past week' in query_lower:
                week_ago = today - timedelta(days=7)
                start_date, end_date = week_ago, today
            elif 'last month' in query_lower or 'past month' in query_lower:
                month_ago = today - timedelta(days=30)
                start_date, end_date = month_ago, today
            elif 'all time' in query_lower or 'all trades' in query_lower:
                start_date, end_date = None, None  # No date filter
            else:
                # Default to today's trades
                start_date, end_date = today, today
            
            # Get data based on date range
            if start_date and end_date:
                trades = self._get_trades_by_date_range(start_date, end_date)
            else:
                trades = self._get_all_trades()
            
            # Let LLM handle the analysis
            return self._generate_intelligent_response(query, trades)
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            return [{"type": "error", "content": f"Error processing query: {str(e)}"}]

    def _get_trades_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get trades within a date range"""
        try:
            from flask import current_app
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Always use current_app context
            if current_app:
                trades = TradeRecord.query.filter(
                    TradeRecord.created_at >= start_datetime,
                    TradeRecord.created_at <= end_datetime,
                    TradeRecord.dv01.isnot(None),
                    TradeRecord.dv01 > 0
                ).all()
            else:
                # This should not happen in production, but fallback
                logger.error("No Flask app context available")
                return []
            
            return [self._trade_to_dict(trade) for trade in trades]
        except Exception as e:
            logger.error(f"Error getting trades by date range: {e}")
            return []

    def _get_all_trades(self) -> List[Dict[str, Any]]:
        """Get all trades"""
        try:
            from flask import current_app
            
            # Always use current_app context
            if current_app:
                trades = TradeRecord.query.filter(
                    TradeRecord.dv01.isnot(None),
                    TradeRecord.dv01 > 0
                ).all()
            else:
                # This should not happen in production, but fallback
                logger.error("No Flask app context available")
                return []
            
            return [self._trade_to_dict(trade) for trade in trades]
        except Exception as e:
            logger.error(f"Error getting all trades: {e}")
            return []

    def _trade_to_dict(self, trade: TradeRecord) -> Dict[str, Any]:
        """Convert TradeRecord to dictionary"""
        return {
            'dissemination_identifier': trade.dissemination_identifier,
            'currency': trade.currency,
            'asset_class': trade.asset_class,
            'notional': float(trade.notionals) if trade.notionals else 0.0,
            'dv01': float(trade.dv01) if trade.dv01 else 0.0,
            'rate': float(trade.rates) if trade.rates else 0.0,
            'effective_date': trade.effective_date.isoformat() if trade.effective_date else None,
            'expiration_date': trade.expiration_date.isoformat() if trade.expiration_date else None,
            'tenor': trade.tenor,
            'action_type': trade.action_type,
            'event_type': trade.event_type,
            'created_at': trade.created_at.isoformat() if trade.created_at else None
        }

    def _generate_intelligent_response(self, query: str, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to understand query intent and generate appropriate response"""
        try:
            if not trades:
                return [{"type": "analysis", "content": "No trades found for the specified criteria."}]
            
            # Try LLM first
            if self.llm_analyzer.is_available():
                try:
                    result = self.llm_analyzer.analyze_trades(trades, query)
                    if result and not result.startswith("Error:"):
                        return [{"type": "analysis", "content": result}]
                except Exception as e:
                    logger.warning(f"LLM analysis failed: {e}")
            
            # Fallback to structured analysis
            result = self.fallback_analyzer.analyze_trades(trades, query)
            return [{"type": "analysis", "content": result}]
            
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            return [{"type": "analysis", "content": f"Error processing query: {str(e)}"}]