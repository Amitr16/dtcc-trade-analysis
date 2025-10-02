# DTCC Trade Analysis Application

## Overview
This is a comprehensive web application that automatically fetches, processes, and analyzes DTCC (Depository Trust & Clearing Corporation) trade data to provide real-time market insights and commentary.

## What It Does

### 🔄 **Automated Data Collection**
- **Fetches trade data** from DTCC API every 60 seconds
- **Handles trade corrections** by replacing modified trades with updated versions
- **Prevents duplicates** using unique dissemination identifiers
- **Stores data** in SQLite database for persistence

### 📊 **Real-Time Analysis**
- **Processes trade data** to identify market structures (Outrights, Spreads, Butterflies)
- **Calculates DV01** (Dollar Value of 01) for risk assessment
- **Generates currency-specific commentary** for major currencies (USD, EUR, GBP, JPY, etc.)
- **Creates market summaries** with trade counts, volumes, and rate levels

### 🤖 **AI-Powered Intelligence (MCP Queries)**
- **Natural language queries** - Ask questions like "Show me EUR trades today" or "What's the market sentiment?"
- **Hybrid analysis model** - Combines structured analysis with LLM-powered insights
- **Google News integration** - Fetches real-time market news for context
- **Intelligent summaries** with:
  - Key insights and observations
  - Trend analysis (yesterday vs today)
  - Market context and news
  - Notable patterns and recommendations

### 📈 **Market Commentary Features**
- **Currency-specific reports** for USD, EUR, GBP, JPY, AUD, SGD, HKD, INR, KRW, TWD, THB
- **Structure analysis** - Outrights, Spreads, Butterflies
- **Rate level tracking** - Spot rates, forward rates, rate ranges
- **Maturity analysis** - Proper display of tenors (1M, 2M, 1Y, 2Y, etc.)
- **DV01 reporting** - Risk metrics in local currency

### 🎯 **Key Capabilities**

#### **For Traders:**
- Real-time market activity monitoring
- Currency-specific trade analysis
- Risk assessment through DV01 calculations
- Market structure identification

#### **For Analysts:**
- Historical trade data export
- Custom date range filtering
- Multi-currency analysis
- Market commentary generation

#### **For Management:**
- Processing status monitoring
- Data quality assurance
- Automated reporting
- Market intelligence summaries

## Technical Architecture

### **Backend (Python/Flask)**
- **Data Processor**: Automated fetching and analysis
- **Database Models**: Trade records, structured trades, commentary, processing logs
- **API Endpoints**: RESTful API for frontend communication
- **Scheduler**: Background tasks for continuous data processing

### **Frontend (HTML/CSS/JavaScript)**
- **Dashboard Interface**: Real-time data visualization
- **MCP Queries**: Natural language interface
- **Filtering System**: Currency and date range selection
- **Export Capabilities**: CSV download for analysis

### **Data Flow**
1. **Fetch** → DTCC API provides raw trade data
2. **Process** → Parse and validate trade information
3. **Store** → Save to SQLite database with deduplication
4. **Analyze** → Generate structured analysis and commentary
5. **Display** → Present insights through web interface
6. **Query** → Enable AI-powered natural language queries

## Use Cases

### **Daily Operations**
- Monitor overnight trading activity
- Track currency-specific market movements
- Identify unusual trading patterns
- Generate morning market briefings

### **Risk Management**
- Calculate portfolio DV01 exposure
- Monitor rate level changes
- Track market structure evolution
- Assess currency concentration

### **Market Intelligence**
- Understand market sentiment
- Track trading volumes and patterns
- Identify emerging trends
- Generate client reports

## Deployment Options

### **Local Development**
- SQLite database for easy setup
- Automatic data collection
- Full feature access
- Real-time updates

### **Production (Render.com)**
- Persistent data storage
- Scalable infrastructure
- Environment variable configuration
- Gunicorn production server

## Key Features

- ✅ **Real-time data** - Updates every 60 seconds
- ✅ **AI-powered analysis** - Natural language queries
- ✅ **Multi-currency support** - 11 major currencies
- ✅ **Market commentary** - Automated report generation
- ✅ **Data export** - CSV download capabilities
- ✅ **Web interface** - Modern, responsive dashboard
- ✅ **Error handling** - Robust error recovery
- ✅ **Production ready** - Scalable deployment

## Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run locally**: `python src/main.py`
3. **Access dashboard**: `http://localhost:5000`
4. **Try MCP queries**: Ask natural language questions about the data
5. **Export data**: Download CSV files for external analysis

This application transforms raw DTCC trade data into actionable market intelligence, making it an essential tool for traders, analysts, and risk managers in the derivatives market.
