"""
LLM-powered analysis service for DTCC trade data
Uses OpenAI API for intelligent analysis and insights
"""

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM-powered analysis for trade data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4"
        self.max_tokens = 2000
        
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.api_key is not None
    
    def analyze_trades(self, trades: List[Dict[str, Any]], query: str) -> str:
        """Analyze trades using LLM"""
        if not self.is_available():
            return "LLM analysis not available - OpenAI API key not configured"
        
        try:
            # Prepare data for LLM
            analysis_data = self._prepare_analysis_data(trades, query)
            
            # Add market news context
            currencies = list(analysis_data['currencies'].keys())
            market_news = self._search_currency_news(currencies)
            analysis_data['market_news'] = market_news
            
            # Generate analysis using LLM
            analysis = self._generate_analysis(analysis_data, query)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return f"Error in LLM analysis: {str(e)}"
    
    def _prepare_analysis_data(self, trades: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Prepare trade data for LLM analysis"""
        if not trades:
            return {"trades": [], "summary": "No trades found"}
        
        # Aggregate data for analysis
        currencies = {}
        total_dv01 = 0
        total_notionals = 0
        tenor_distribution = {}
        asset_classes = {}
        
        for trade in trades:
            currency = trade.get('currency', 'Unknown')
            dv01 = trade.get('dv01', 0)
            notionals = trade.get('notionals', 0)
            tenor = trade.get('tenor', 0)
            asset_class = trade.get('asset_class', 'Unknown')
            
            # Aggregate by currency
            if currency not in currencies:
                currencies[currency] = {'count': 0, 'dv01': 0, 'notionals': 0}
            currencies[currency]['count'] += 1
            currencies[currency]['dv01'] += dv01
            currencies[currency]['notionals'] += notionals
            
            total_dv01 += dv01
            total_notionals += notionals
            
            # Tenor distribution
            tenor_key = f"{tenor:.1f}Y" if tenor >= 1 else f"{tenor*12:.0f}M"
            tenor_distribution[tenor_key] = tenor_distribution.get(tenor_key, 0) + 1
            
            # Asset class distribution
            asset_classes[asset_class] = asset_classes.get(asset_class, 0) + 1
        
        return {
            "query": query,
            "total_trades": len(trades),
            "total_dv01": total_dv01,
            "total_notionals": total_notionals,
            "currencies": currencies,
            "tenor_distribution": tenor_distribution,
            "asset_classes": asset_classes,
            "sample_trades": trades[:5]  # Include sample trades for context
        }
    
    def _generate_analysis(self, data: Dict[str, Any], query: str) -> str:
        """Generate analysis using OpenAI API"""
        try:
            import openai
            
            # Set up OpenAI client
            client = openai.OpenAI(api_key=self.api_key)
            
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(data, query)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior financial analyst specializing in interest rate derivatives and DTCC trade data. You MUST follow the exact format specified in the user's prompt. Always use the structured format with numbered sections and subsections as requested. Provide clear, professional analysis with specific insights and actionable observations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            # Fall back to structured analysis
            from src.services.llm_analyzer import FallbackAnalyzer
            fallback = FallbackAnalyzer()
            return fallback.analyze_trades(data['sample_trades'], query)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fall back to structured analysis
            from src.services.llm_analyzer import FallbackAnalyzer
            fallback = FallbackAnalyzer()
            return fallback.analyze_trades(data['sample_trades'], query)
    
    def _create_analysis_prompt(self, data: Dict[str, Any], query: str) -> str:
        """Create analysis prompt for LLM"""
        prompt = f"""
Analyze the following DTCC trade data and provide insights based on the user's query: "{query}"

Trade Data Summary:
- Total Trades: {data['total_trades']}
- Total DV01: {data['total_dv01']:,.2f}
- Total Notionals: {data['total_notionals']:,.2f}

Currency Breakdown:
"""
        
        for currency, stats in data['currencies'].items():
            prompt += f"- {currency}: {stats['count']} trades, DV01: {stats['dv01']:,.2f}, Notionals: {stats['notionals']:,.2f}\n"
        
        prompt += f"""
Tenor Distribution: {data['tenor_distribution']}
Asset Classes: {data['asset_classes']}

Sample Trades:
"""
        
        for trade in data['sample_trades']:
            prompt += f"- {trade.get('currency', 'N/A')} {trade.get('tenor', 0):.1f}Y, DV01: {trade.get('dv01', 0):.2f}, Rate: {trade.get('rates', 0):.4f}\n"
        
        # Add market news if available
        if 'market_news' in data:
            prompt += f"""
Market Context:
{data['market_news']}
"""
        
        prompt += f"""
CRITICAL: You MUST format your response EXACTLY as follows. Do NOT use any other format:

## 1. Key Insights and Observations
- Insight 1: [Specific observation about trading activity]
- Insight 2: [Specific observation about risk levels]
- Insight 3: [Specific observation about notable characteristics]

## 2. Trend Analysis
### Yesterday vs Today
[Compare yesterday's activity to today's - mention specific changes in volume, DV01, or patterns]

### Last Week vs Today  
[Compare last week's trends to today's activity - highlight any significant shifts or developments]

### Week-over-Week Comparison
[Analyze the broader trend over the past week and how it relates to today's activity]

## 3. Market Context and News
[Include relevant market developments that could explain the trading patterns]

## 4. Notable Patterns and Trends
[Identify specific patterns in tenor distribution, currency concentration, or other structural elements]

## 5. Risk Assessment and Recommendations
[Provide specific risk concerns and actionable recommendations for traders and risk managers]

IMPORTANT: Start your response with "## 1. Key Insights and Observations" and follow the exact format above. Do not use any other formatting or structure.
"""
        
        return prompt
    
    def _search_currency_news(self, currencies: List[str]) -> str:
        """Search for recent news related to the currencies using Google News"""
        try:
            # Get the primary currency (most traded)
            primary_currency = currencies[0] if currencies else "USD"
            
            # Create search terms for Google News
            search_terms = f"{primary_currency} interest rates derivatives news"
            
            # Google News search URL
            search_url = f"https://news.google.com/search?q={urllib.parse.quote(search_terms)}&hl=en&gl=US&ceid=US:en"
            
            # Headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make request to Google News
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract news headlines and snippets
            news_items = []
            
            # Look for article elements (Google News structure)
            articles = soup.find_all('article', limit=5)
            
            for article in articles:
                # Try to find headline
                headline_elem = article.find('h3') or article.find('h4') or article.find('a')
                if headline_elem:
                    headline = headline_elem.get_text(strip=True)
                    if headline and len(headline) > 10:  # Filter out very short headlines
                        news_items.append(headline)
            
            # If no articles found, try alternative selectors
            if not news_items:
                # Try different selectors for Google News
                for selector in ['[data-n-tid]', '.JtKRv', '.gPFEn']:
                    elements = soup.select(selector)
                    for elem in elements[:3]:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 20 and len(text) < 200:
                            news_items.append(text)
                            if len(news_items) >= 3:
                                break
                    if news_items:
                        break
            
            # Format the news results
            if news_items:
                news_summary = f"Recent market developments for {primary_currency}:\n\n"
                for i, item in enumerate(news_items[:3], 1):
                    news_summary += f"{i}. {item}\n"
                news_summary += f"\n[Source: Google News search for '{search_terms}']"
                return news_summary
            else:
                return f"Recent market developments for {primary_currency}: No recent news found for {primary_currency} interest rate derivatives. [Searched: Google News]"
            
        except requests.RequestException as e:
            logger.error(f"Error fetching news from Google: {e}")
            return f"Market context for {currencies[0] if currencies else 'trading'}: Unable to fetch recent news due to network issues."
        except Exception as e:
            logger.error(f"Error searching for currency news: {e}")
            return f"Market context for {currencies[0] if currencies else 'trading'}: Unable to fetch recent news at this time."

# Fallback analyzer for when LLM is not available
class FallbackAnalyzer:
    """Fallback analyzer using existing DTCCAnalysis logic"""
    
    def __init__(self):
        self.dtcc_analyzer = None
    
    def analyze_trades(self, trades: List[Dict[str, Any]], query: str) -> str:
        """Generate analysis using basic aggregation"""
        try:
            if not trades:
                return "No trades found for analysis"
            
            # Basic aggregation and analysis
            total_trades = len(trades)
            total_dv01 = sum(trade.get('dv01', 0) for trade in trades)
            total_notionals = sum(trade.get('notionals', 0) for trade in trades)
            
            # Group by currency
            currencies = {}
            for trade in trades:
                currency = trade.get('currency', 'Unknown')
                if currency not in currencies:
                    currencies[currency] = {'count': 0, 'dv01': 0, 'notionals': 0}
                currencies[currency]['count'] += 1
                currencies[currency]['dv01'] += trade.get('dv01', 0)
                currencies[currency]['notionals'] += trade.get('notionals', 0)
            
            # Generate analysis
            analysis = f"""
**Trade Analysis Summary**

📊 **Overview:**
- Total Trades: {total_trades:,}
- Total DV01: {total_dv01:,.2f}
- Total Notionals: {total_notionals:,.2f}

💱 **Currency Breakdown:**
"""
            
            for currency, stats in currencies.items():
                percentage = (stats['count'] / total_trades) * 100
                analysis += f"- **{currency}**: {stats['count']} trades ({percentage:.1f}%), DV01: {stats['dv01']:,.2f}, Notionals: {stats['notionals']:,.2f}\n"
            
            analysis += f"""
📈 **Key Metrics:**
- Average DV01 per trade: {total_dv01/total_trades:.2f}
- Average Notionals per trade: {total_notionals/total_trades:,.2f}

🔍 **Analysis:**
Based on the trading data, this represents significant market activity with substantial DV01 exposure across multiple currencies. The concentration and distribution suggest active risk management and hedging activities.
"""
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {e}")
            return f"Analysis error: {str(e)}"
    
    def generate_summary(self, trades: List[Dict[str, Any]], query: str) -> str:
        """Generate summary using basic aggregation"""
        if not trades:
            return "No trades found"
        
        # Basic aggregation
        total_trades = len(trades)
        total_dv01 = sum(trade.get('dv01', 0) for trade in trades)
        total_notionals = sum(trade.get('notionals', 0) for trade in trades)
        
        currencies = {}
        for trade in trades:
            currency = trade.get('currency', 'Unknown')
            currencies[currency] = currencies.get(currency, 0) + 1
        
        summary = f"""
**Trade Summary for: {query}**

📊 **Overview:**
- Total Trades: {total_trades:,}
- Total DV01: {total_dv01:,.2f}
- Total Notionals: {total_notionals:,.2f}

💱 **Currency Breakdown:**
"""
        
        for currency, count in currencies.items():
            percentage = (count / total_trades) * 100
            summary += f"- {currency}: {count} trades ({percentage:.1f}%)\n"
        
        summary += f"""
📈 **Key Metrics:**
- Average DV01 per trade: {total_dv01/total_trades:.2f}
- Average Notionals per trade: {total_notionals/total_trades:,.2f}
"""
        
        return summary
