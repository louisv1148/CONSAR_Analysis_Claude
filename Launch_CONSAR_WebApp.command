#!/bin/bash

# CONSAR Analysis Web App Launcher
# Double-click this file to start the web application

echo "🚀 Starting CONSAR Analysis Web App..."
echo "This will open the web interface in your browser"
echo ""

# Always change to the main CONSAR directory regardless of where launcher is located
CONSAR_DIR="/Users/lvc/CONSAR_Analysis_Claude"
cd "$CONSAR_DIR"

echo "📁 Working directory: $CONSAR_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found at: $CONSAR_DIR/venv"
    echo "Please ensure you're in the correct directory with the venv folder"
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing required packages..."
    pip install -r requirements_app.txt
fi

# Start the web app
echo "🌐 Starting web application..."
echo "The app will open in your browser automatically"
echo ""
echo "📍 Local URL: http://localhost:8501"
echo ""
echo "🛑 To stop the app: Close this window or press Ctrl+C"
echo "==============================================="

# Launch Streamlit app
streamlit run consar_app.py

echo ""
echo "👋 CONSAR Analysis Web App stopped"
echo "Press any key to close this window..."
read -n 1