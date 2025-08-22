#!/bin/bash
# CONSAR Monitor Startup Script

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -f ../venv/bin/activate ]; then
    source ../venv/bin/activate
fi

# Run the monitor
python3 consar_monitor.py "$@"