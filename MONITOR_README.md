# CONSAR Data Monitor

Automated monitoring system for CONSAR (Mexican pension fund) data updates with human approval workflow.

## 🎯 Overview

This system automatically:
1. **Monitors** CONSAR URLs daily for new data
2. **Downloads & Processes** new data using your existing tools
3. **Emails you** with new records for approval
4. **Waits for your approval** before updating the database
5. **Maintains backups** and prevents corruption

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   URL Monitor   │    │   Data Pipeline  │    │ Human Approval  │
│                 │    │                  │    │                 │
│ 1. Check URLs   │───▶│ 1. Download HTML │───▶│ 1. Email alert  │
│ 2. Detect hash  │    │ 2. Parse → JSON  │    │ 2. Review data  │
│ 3. Flag changes │    │ 3. Download FX   │    │ 3. Approve/Reject│
│                 │    │ 4. Calculate USD │    │ 4. Merge to DB  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r monitor_requirements.txt

# Configure email and directories
python3 setup_monitor.py

# Test the monitor
./run_monitor.sh --run-once
```

### 2. Daily Usage

**When you receive an email notification:**

```bash
# Review the new data
./run_monitor.sh --review approval_20250812_143022

# Approve the changes
./run_monitor.sh --approve approval_20250812_143022

# Or reject them
./run_monitor.sh --reject approval_20250812_143022
```

**Check status anytime:**
```bash
# List pending approvals
./run_monitor.sh --list-pending

# Run manual check
./run_monitor.sh --run-once

# Start continuous monitoring
./run_monitor.sh
```

## 📧 Email Workflow

When new CONSAR data is detected, you'll receive an email with:

- **Summary** of new records by period and Afore
- **Sample records** showing the actual data
- **Attachment** with complete JSON file
- **Approval commands** ready to copy/paste

Example email:
```
Subject: CONSAR Data Update Approval Required - 156 new records

New CONSAR data has been processed and is ready for approval.

SUMMARY:
Total new records: 156

Period 2025-07:
  - Records: 156
  - Afores: Azteca, Banamex, Coppel, Inbursa, Invercap, ...
  - Concepts: Total de Activo, Inversión en Fondos Mutuos, ...

APPROVAL COMMANDS:
To approve: python3 consar_monitor.py --approve approval_20250812_143022
To reject:  python3 consar_monitor.py --reject approval_20250812_143022
```

## 🛡️ Safety Features

### Database Protection
- **Automatic backups** before any changes
- **Validation** of new records
- **Rollback capability** if issues occur
- **Retention policy** (30 days default)

### Change Detection
- **Hash-based monitoring** detects actual content changes
- **Deduplication** prevents duplicate records
- **Format validation** ensures data integrity

### Human Oversight
- **No automatic merging** - requires your approval
- **Detailed previews** of all changes
- **Approval tracking** with audit trail

## ⚙️ Configuration

### Email Settings (Required)
Set these environment variables or add to `.env`:
```bash
CONSAR_EMAIL_USER=your-gmail@gmail.com
CONSAR_EMAIL_PASSWORD=your-app-password
CONSAR_NOTIFY_EMAIL=notifications@example.com
```

### Monitoring Settings (Optional)
```bash
CONSAR_CHECK_INTERVAL_HOURS=24    # How often to check
CONSAR_RETENTION_DAYS=30          # Backup retention
```

### Tool Paths
Update paths in `consar_monitor.py` if your tools are in different locations:
```python
DOWNLOADER_PATH = "/path/to/afore_downloader.py"
PROCESSOR_PATH = "/path/to/process_consar_reports.py"
FX_DOWNLOADER_PATH = "/path/to/banxico_fx_downloader.py"
USD_CONVERTER_PATH = "/path/to/convert_to_usd_simple.py"
```

## 📅 Automation Options

### Option 1: Cron (Local)
```bash
# Edit crontab
crontab -e

# Add daily check at 9 AM
0 9 * * * cd /path/to/CONSAR_Analysis_Claude && ./run_monitor.sh --run-once
```

### Option 2: GitHub Actions (Cloud)
The monitor includes GitHub Actions workflow that runs daily in the cloud:

1. **Set secrets** in your GitHub repo:
   - `CONSAR_EMAIL_USER`
   - `CONSAR_EMAIL_PASSWORD` 
   - `CONSAR_NOTIFY_EMAIL`

2. **Push to GitHub** - workflow runs automatically

3. **Monitor Actions tab** for execution logs

## 📁 File Structure

```
CONSAR_Analysis_Claude/
├── consar_monitor.py           # Main monitoring script
├── setup_monitor.py            # Setup and configuration
├── run_monitor.sh              # Startup script
├── monitor_requirements.txt    # Python dependencies
├── MONITOR_README.md          # This file
├── .env                       # Email configuration (not in git)
├── data/
│   ├── monitor_state.json     # Monitoring state
│   ├── backups/               # Database backups
│   └── pending_approvals/     # Approval packages
├── logs/
│   └── consar_monitor.log     # Monitor logs
└── .github/workflows/
    └── consar_monitor.yml     # GitHub Actions workflow
```

## 🔧 Troubleshooting

### Common Issues

**No email received:**
```bash
# Check email configuration
python3 -c "import os; print('Email user:', os.getenv('CONSAR_EMAIL_USER'))"

# Test email settings
python3 setup_monitor.py  # Re-configure if needed
```

**Processing pipeline fails:**
```bash
# Check tool paths
ls -la /Users/lvc/Consar_downloader_2.0/afore_downloader.py
ls -la /Users/lvc/Consar_report_processing/process_consar_reports.py

# Check logs
tail -f logs/consar_monitor.log
```

**No updates detected:**
```bash
# Force a check (ignores hash comparison)
./run_monitor.sh --run-once

# Check last update time
cat data/monitor_state.json | grep last_check
```

### Logs and Monitoring

- **Monitor logs**: `logs/consar_monitor.log`
- **State file**: `data/monitor_state.json`
- **Backup directory**: `data/backups/`
- **Approval packages**: `data/pending_approvals/`

## 🔐 Security

### Sensitive Data
- ✅ `.env` file excluded from git
- ✅ Email passwords use app-specific passwords
- ✅ Approval files cleaned up after processing
- ✅ Restrictive file permissions

### Best Practices
- Use Gmail App Passwords (not regular password)
- Keep `.env` file secure
- Review all approvals carefully
- Monitor logs for anomalies

## 📊 Monitoring Dashboard

### Check System Status
```bash
# Overall status
./run_monitor.sh --list-pending

# Recent activity
tail -20 logs/consar_monitor.log

# Database stats
python3 -c "
import json
with open('data/merged_consar_data_2019_2025.json') as f:
    data = json.load(f)
print(f'Total records: {len(data):,}')
periods = set(f\"{r['PeriodYear']}-{r['PeriodMonth']}\" for r in data)
print(f'Periods covered: {min(periods)} to {max(periods)}')
"
```

## 🚀 Advanced Usage

### Custom Processing
The monitor can be extended for custom processing:

```python
# Custom validation
def validate_new_records(records):
    # Add your validation logic
    return True

# Custom notifications  
def send_slack_notification(records):
    # Add Slack integration
    pass
```

### Integration with Analysis Tools
```bash
# After approval, automatically update growth analysis
./run_monitor.sh --approve approval_123 && python3 growth_analysis.py
```

## 📞 Support

For issues:
1. Check logs: `tail -f logs/consar_monitor.log`
2. Review state: `cat data/monitor_state.json`
3. Test components individually
4. Check GitHub Issues for known problems

---

**🤖 Built for reliable, safe automation of CONSAR data updates with human oversight.**