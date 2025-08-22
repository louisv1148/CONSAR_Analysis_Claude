#!/bin/bash

# CONSAR Analysis App Launcher
# This script validates the definitive database and starts the Streamlit web application

echo "🚀 Starting CONSAR Analysis Web App..."

# Activate virtual environment
source ../venv/bin/activate

# Validate definitive database integrity
echo "🔍 Validating definitive database..."
python ../scripts/data_processing/validate_definitive_db.py

# Check if validation passed
if [ $? -ne 0 ]; then
    echo "❌ Database validation failed - cannot start app"
    echo "🔧 Please run: python ../scripts/data_processing/fix_database_consistency.py"
    exit 1
fi

echo "✅ Database validated successfully"
echo "📊 Loading interface..."

# Install/update dependencies if needed
pip install -q -r ../config/requirements/webapp.txt

# Start the Streamlit app
echo ""
echo "🌐 Starting web server..."
echo "📱 App will be available at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the app"
echo ""

streamlit run consar_app.py