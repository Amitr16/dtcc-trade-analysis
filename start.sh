#!/bin/bash

# DTCC Trade Analysis Web Application Startup Script

echo "🚀 Starting DTCC Trade Analysis Web Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import flask, pandas, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

# Create database directory if it doesn't exist
mkdir -p src/database

# Start the application
echo "🌐 Starting web application on http://localhost:5000"
echo "📊 Dashboard will be available at: http://localhost:5000"
echo "🔄 Automated data collection will start immediately"
echo ""
echo "Press Ctrl+C to stop the application"
echo "----------------------------------------"

python src/main.py

