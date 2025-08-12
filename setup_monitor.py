#!/usr/bin/env python3
"""
CONSAR Monitor Setup Script

Sets up the monitoring system with proper configuration and environment.
"""

import os
import sys
import json
import getpass
from pathlib import Path

def setup_email_config():
    """Configure email settings for notifications."""
    print("📧 EMAIL CONFIGURATION")
    print("="*50)
    print("For Gmail, you'll need an 'App Password' (not your regular password)")
    print("Instructions: https://support.google.com/mail/answer/185833")
    print()
    
    email_user = input("Your Gmail address: ").strip()
    
    print("Your App Password (input will be hidden):")
    email_password = getpass.getpass()
    
    notify_email = input(f"Email to send notifications to [{email_user}]: ").strip()
    if not notify_email:
        notify_email = email_user
        
    return email_user, email_password, notify_email

def create_env_file(email_user, email_password, notify_email):
    """Create .env file with configuration."""
    env_content = f"""# CONSAR Monitor Environment Configuration
# Email settings for notifications
CONSAR_EMAIL_USER={email_user}
CONSAR_EMAIL_PASSWORD={email_password}
CONSAR_NOTIFY_EMAIL={notify_email}

# Optional: Customize monitoring settings
# CONSAR_CHECK_INTERVAL_HOURS=24
# CONSAR_RETENTION_DAYS=30
"""
    
    env_path = Path(".env")
    with open(env_path, 'w') as f:
        f.write(env_content)
        
    # Set restrictive permissions on .env file
    os.chmod(env_path, 0o600)
    
    print(f"✅ Created {env_path} with email configuration")
    return env_path

def create_gitignore():
    """Create/update .gitignore to exclude sensitive files."""
    gitignore_path = Path(".gitignore")
    
    gitignore_additions = [
        "# CONSAR Monitor",
        ".env",
        "data/monitor_state.json",
        "data/pending_approvals/",
        "data/backups/",
        "temp_processing/",
        "logs/",
        "__pycache__/",
        "*.pyc"
    ]
    
    existing_lines = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_lines = set(line.strip() for line in f)
    
    new_lines = []
    for line in gitignore_additions:
        if line not in existing_lines:
            new_lines.append(line)
    
    if new_lines:
        with open(gitignore_path, 'a') as f:
            f.write("\\n" + "\\n".join(new_lines) + "\\n")
        print(f"✅ Updated {gitignore_path}")
    else:
        print(f"✅ {gitignore_path} already up to date")

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/backups",
        "data/pending_approvals", 
        "temp_processing",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def create_startup_script():
    """Create startup script for easy launching."""
    script_content = '''#!/bin/bash
# CONSAR Monitor Startup Script

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Run the monitor
python3 consar_monitor.py "$@"
'''
    
    script_path = Path("run_monitor.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)
        
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Created {script_path}")
    return script_path

def create_cron_example():
    """Create example cron job configuration."""
    cron_content = f"""# CONSAR Monitor - Daily Check at 9 AM
# Add this line to your crontab: crontab -e

0 9 * * * cd {Path.cwd()} && ./run_monitor.sh --run-once >> logs/cron.log 2>&1

# To check current cron jobs: crontab -l
# To edit cron jobs: crontab -e
"""
    
    cron_path = Path("cron_example.txt")
    with open(cron_path, 'w') as f:
        f.write(cron_content)
        
    print(f"✅ Created {cron_path}")
    return cron_path

def verify_dependencies():
    """Check if existing tools are accessible."""
    tools = {
        "CONSAR Downloader": "/Users/lvc/Consar_downloader_2.0/afore_downloader.py",
        "CONSAR Processor": "/Users/lvc/Consar_report_processing/process_consar_reports.py", 
        "FX Downloader": "/Users/lvc/Banxico_FX_Update/banxico_fx_downloader.py",
        "USD Converter": "/Users/lvc/Banxico_FX_Update/convert_to_usd_simple.py"
    }
    
    print("\\n🔍 VERIFYING EXISTING TOOLS")
    print("="*50)
    
    all_good = True
    for name, path in tools.items():
        if Path(path).exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: NOT FOUND at {path}")
            all_good = False
            
    return all_good

def main():
    """Main setup routine."""
    print("🚀 CONSAR MONITOR SETUP")
    print("="*50)
    print("This will configure the CONSAR monitoring system.")
    print()
    
    # Verify dependencies first
    if not verify_dependencies():
        print("\\n❌ Some required tools are missing. Please check paths in consar_monitor.py")
        return False
    
    # Create directories
    print("\\n📁 CREATING DIRECTORIES")
    print("="*30)
    create_directories()
    
    # Setup email
    print("\\n📧 EMAIL SETUP")
    print("="*30)
    email_user, email_password, notify_email = setup_email_config()
    env_path = create_env_file(email_user, email_password, notify_email)
    
    # Create supporting files
    print("\\n📝 CREATING SUPPORT FILES")
    print("="*30)
    create_gitignore()
    script_path = create_startup_script()
    cron_path = create_cron_example()
    
    # Final instructions
    print("\\n🎉 SETUP COMPLETE!")
    print("="*50)
    print("\\nNext steps:")
    print(f"1. Test the monitor: ./run_monitor.sh --run-once")
    print(f"2. List any pending approvals: ./run_monitor.sh --list-pending")
    print(f"3. Set up daily automation: see {cron_path}")
    print("\\nDevelopment commands:")
    print("- Review approval: ./run_monitor.sh --review <approval_id>")
    print("- Approve changes: ./run_monitor.sh --approve <approval_id>")
    print("- Reject changes: ./run_monitor.sh --reject <approval_id>")
    print("\\nContinuous monitoring:")
    print("- Start monitoring: ./run_monitor.sh")
    print("- Stop with Ctrl+C")
    print()
    print("⚠️  Remember: Keep your .env file secure and never commit it to git!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)