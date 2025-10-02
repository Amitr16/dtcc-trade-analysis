# DTCC Trade Analysis Web Application

## Overview
A complete web application that automatically runs DTCC data collection and analysis every minute, builds historical data, and provides a dynamic web interface for viewing market commentaries with currency and date filtering.

## Features

### 🔄 Automated Data Processing
- **Every Minute**: Automatically fetches new trade data from DTCC API
- **Duplicate Detection**: Prevents duplicate trade records
- **Historical Storage**: Builds comprehensive historical database
- **Error Handling**: Robust error handling and logging

### 📊 Trade Analysis
- **Structure Detection**: Identifies spreads, butterflies, outrights, and unwinds
- **DV01 Validation**: Ensures multi-leg structures are delta-neutral
- **Market Commentary**: Professional market commentary generation
- **Multi-Currency Support**: USD, EUR, GBP, JPY, INR, SGD, AUD, THB, TWD, KRW, HKD

### 🌐 Web Interface
- **Modern UI**: Professional, responsive design
- **Real-time Updates**: Auto-refreshes every 2 minutes
- **Force Refresh Button**: Manual refresh that reruns scripts and reloads page
- **Advanced Filtering**: Multi-select currencies and date ranges
- **Quick Select Options**: Major currencies, Asian currencies, select all, clear all
- **Date Quick Select**: Today, last 7 days, last 30 days
- **Multiple Views**: Grouped by date or by currency
- **Processing Status**: Live monitoring of data collection

## Architecture

### Backend Components
```
src/
├── main.py                    # Flask application entry point
├── models/
│   └── trade_data.py         # Database models (SQLAlchemy)
├── routes/
│   └── api.py                # REST API endpoints
├── services/
│   └── data_processor.py     # Automated data processing
├── DTCCParser.py             # DTCC API data fetching
├── DTCCAnalysis.py           # Trade analysis and commentary
└── static/                   # Frontend files
    ├── index.html            # Main web interface
    ├── styles.css            # Modern CSS styling
    └── app.js                # JavaScript application logic
```

### Database Schema
- **TradeRecord**: Individual trade data from DTCC
- **StructuredTrade**: Analyzed trade structures
- **Commentary**: Generated market commentary
- **ProcessingLog**: System monitoring and logs

## Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment support

### Quick Start
```bash
# Navigate to project directory
cd dtcc-analysis-app

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python src/main.py
```

### Manual Setup
```bash
# Install required packages
pip install flask flask-cors flask-sqlalchemy requests pandas numpy

# Update requirements
pip freeze > requirements.txt

# Run application
python src/main.py
```

## API Endpoints

### Commentary & Data
- `GET /api/commentary` - Get market commentary with filters
- `GET /api/currencies` - Get available currencies
- `GET /api/date-range` - Get available date range
- `GET /api/summary` - Get summary statistics
- `GET /api/structured-trades` - Get structured trade data

### System Management
- `GET /api/status` - Get processing status and logs
- `POST /api/manual-run` - Trigger manual data collection/analysis
- `POST /api/manual-refresh` - Force refresh data and reload page

### Query Parameters
```javascript
// Commentary endpoint example
/api/commentary?currencies=USD&currencies=EUR&start_date=2025-01-01&end_date=2025-01-31
```

## Web Interface Features

### Filters Section
- **Multi-Select Currencies**: Choose multiple currencies simultaneously
- **Date Range Picker**: Select custom date ranges
- **Apply/Reset Buttons**: Easy filter management
- **Manual Run**: Trigger immediate data processing

### Summary Cards
- **Total Trades**: Count of trades in selected period
- **Total DV01**: Aggregated DV01 exposure
- **Active Currencies**: Number of currencies with activity
- **Last Update**: Timestamp of latest data refresh

### Commentary Display
- **Grouped by Date**: Default view showing trades by date
- **By Currency**: Alternative view organized by currency
- **Professional Format**: Market-standard commentary formatting
- **Trade Statistics**: Count and DV01 summaries per currency

### Processing Status
- **Live Monitoring**: Real-time processing status
- **Recent Logs**: Last 10 processing runs
- **Success/Error Indicators**: Visual status indicators
- **Execution Times**: Performance monitoring

## Configuration

### Environment Variables
```bash
# Optional: Set custom database path
export DATABASE_URL="sqlite:///custom_path/app.db"

# Optional: Set custom port
export PORT=5000

# Optional: Enable debug mode
export FLASK_DEBUG=True
```

### Processing Settings
```python
# In data_processor.py
REFRESH_INTERVAL = 60  # seconds (1 minute)
AUTO_REFRESH_UI = 120  # seconds (2 minutes)
MAX_LOGS_DISPLAY = 10  # recent logs to show
```

## Data Flow

### 1. Data Collection (Every Minute)
```
DTCC API → DTCCParser.py → TradeRecord (Database)
```

### 2. Analysis Processing (Every Minute)
```
TradeRecord → DTCCAnalysis.py → StructuredTrade + Commentary (Database)
```

### 3. Web Interface (Real-time)
```
Database → API Endpoints → JavaScript → User Interface
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check virtual environment
which python  # Should point to venv

# Check dependencies
pip list | grep flask
```

#### No Data Appearing
```bash
# Check DTCC API connectivity
curl "https://pddata.dtcc.com/ppd/api/ticker/CFTC/RATES"

# Check database
sqlite3 src/database/app.db ".tables"

# Check logs
tail -f application.log
```

#### Processing Errors
```bash
# Check processing status via API
curl http://localhost:5000/api/status

# Manual run to test
curl -X POST http://localhost:5000/api/manual-run \
  -H "Content-Type: application/json" \
  -d '{"type": "both"}'
```

### Debug Mode
```bash
# Run with debug output
FLASK_DEBUG=True python src/main.py

# Check browser console for JavaScript errors
# Open Developer Tools → Console
```

## Deployment

### Local Development
```bash
python src/main.py
# Access: http://localhost:5000
```

### Production Deployment
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app

# Using Flask built-in (development only)
python src/main.py
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
EXPOSE 5000
CMD ["python", "src/main.py"]
```

## Monitoring & Maintenance

### Health Checks
- **Processing Status**: Monitor via `/api/status` endpoint
- **Database Size**: Check SQLite file growth
- **Memory Usage**: Monitor Python process memory
- **API Response Times**: Track endpoint performance

### Data Retention
```sql
-- Clean old logs (optional)
DELETE FROM processing_logs WHERE run_timestamp < date('now', '-30 days');

-- Archive old trades (optional)
-- Implement based on storage requirements
```

### Backup Strategy
```bash
# Backup database
cp src/database/app.db backups/app_$(date +%Y%m%d).db

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp src/database/app.db "backups/app_backup_$DATE.db"
find backups/ -name "app_backup_*.db" -mtime +7 -delete
```

## Performance Optimization

### Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX idx_trade_time ON trade_records(trade_time);
CREATE INDEX idx_currency ON trade_records(currency);
CREATE INDEX idx_analysis_date ON structured_trades(analysis_date);
```

### Memory Management
```python
# In data_processor.py
# Process data in chunks for large datasets
CHUNK_SIZE = 1000
```

### Caching
```python
# Implement Redis caching for API responses
# Cache commentary data for 5 minutes
# Cache summary data for 2 minutes
```

## Security Considerations

### API Security
- **CORS Configuration**: Properly configured for frontend access
- **Input Validation**: All user inputs validated
- **SQL Injection Prevention**: Using SQLAlchemy ORM
- **Rate Limiting**: Consider implementing for production

### Data Privacy
- **No Personal Data**: Only market data processed
- **Secure Storage**: SQLite database with proper permissions
- **Audit Trail**: All processing activities logged

## Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd dtcc-analysis-app

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development server
python src/main.py
```

### Code Style
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features
- **CSS**: BEM methodology for class naming
- **Documentation**: Comprehensive docstrings

## License
This project is licensed under the MIT License.

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Test API endpoints manually
4. Check browser console for frontend issues

---

**Built with**: Flask, SQLAlchemy, Pandas, JavaScript, HTML5, CSS3

