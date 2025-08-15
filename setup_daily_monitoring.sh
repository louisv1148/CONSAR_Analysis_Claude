#!/bin/bash

# CONSAR Daily Monitoring Setup Script
# This script sets up a cron job to run CONSAR monitoring daily at 9 AM

echo "🔧 Setting up daily CONSAR monitoring..."

# Create the cron job script
cat > /Users/lvc/CONSAR_Analysis_Claude/daily_monitor.sh << 'EOF'
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

# Run the monitoring check
python3 consar_monitor.py --run-once >> logs/daily_monitor.log 2>&1

# Log completion
echo "=== COMPLETED: $(date) ===" >> logs/daily_monitor.log
echo "" >> logs/daily_monitor.log
EOF

# Make the script executable
chmod +x /Users/lvc/CONSAR_Analysis_Claude/daily_monitor.sh

echo "✅ Created daily monitor script at: /Users/lvc/CONSAR_Analysis_Claude/daily_monitor.sh"

# Create logs directory if it doesn't exist
mkdir -p /Users/lvc/CONSAR_Analysis_Claude/logs

echo ""
echo "📋 NEXT STEPS:"
echo "1. Run this command to add the cron job:"
echo ""
echo "   (crontab -l 2>/dev/null; echo '0 9 * * * /Users/lvc/CONSAR_Analysis_Claude/daily_monitor.sh') | crontab -"
echo ""
echo "2. To verify the cron job was added:"
echo ""
echo "   crontab -l"
echo ""
echo "3. To check daily monitor logs:"
echo ""
echo "   tail -f /Users/lvc/CONSAR_Analysis_Claude/logs/daily_monitor.log"
echo ""
echo "4. To remove the cron job later (if needed):"
echo ""
echo "   crontab -l | grep -v 'daily_monitor.sh' | crontab -"
echo ""
echo "⏰ The monitor will run every day at 9:00 AM"
echo "📧 You'll receive email notifications when new data is found"
echo ""