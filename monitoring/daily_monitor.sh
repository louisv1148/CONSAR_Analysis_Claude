#!/bin/bash

# Daily CONSAR Monitor Script
# This script runs the CONSAR monitoring system with proper environment setup

# Set environment variables
export CONSAR_EMAIL_USER="lvcshopping@gmail.com"
export CONSAR_EMAIL_PASSWORD="qpen mxwf tbop fuhr"
export CONSAR_NOTIFY_EMAIL="lvcshopping@gmail.com"

# Change to the correct directory
cd /Users/lvc/CONSAR_Analysis_Claude

# Add timestamp to log
echo "=== DAILY MONITOR RUN: $(date) ===" >> logs/daily_monitor.log

# Use absolute path for python and ensure packages are available
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
pip3 install requests beautifulsoup4 >/dev/null 2>&1
python3 monitoring/consar_monitor.py --run-once >> logs/daily_monitor.log 2>&1

# Log completion
echo "=== COMPLETED: $(date) ===" >> logs/daily_monitor.log
echo "" >> logs/daily_monitor.log
