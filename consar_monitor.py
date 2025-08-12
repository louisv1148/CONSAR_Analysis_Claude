#!/usr/bin/env python3
"""
CONSAR Data Monitor

Monitors CONSAR URLs daily for new data and triggers automated processing
when new data is detected. Includes human approval workflow via email.

Features:
- Daily URL monitoring for new data
- Automated processing using existing tools
- Email notifications with approval workflow
- Database backup and validation safeguards
- Cloud-ready architecture (local or GitHub Actions)
"""

import os
import json
import hashlib
import smtplib
import time
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# === CONFIGURATION ===
class Config:
    # Paths to existing tools
    DOWNLOADER_PATH = "/Users/lvc/Consar_downloader_2.0/afore_downloader.py"
    PROCESSOR_PATH = "/Users/lvc/Consar_report_processing/process_consar_reports.py"
    FX_DOWNLOADER_PATH = "/Users/lvc/Banxico_FX_Update/banxico_fx_downloader.py"
    USD_CONVERTER_PATH = "/Users/lvc/Banxico_FX_Update/convert_to_usd_simple.py"
    
    # Database paths
    CURRENT_DB_PATH = "/Users/lvc/CONSAR_Analysis_Claude/data/merged_consar_data_2019_2025.json"
    BACKUP_DIR = "/Users/lvc/CONSAR_Analysis_Claude/data/backups"
    
    # Working directories
    TEMP_DIR = "/Users/lvc/CONSAR_Analysis_Claude/temp_processing"
    MONITOR_STATE_FILE = "/Users/lvc/CONSAR_Analysis_Claude/data/monitor_state.json"
    PENDING_APPROVALS_DIR = "/Users/lvc/CONSAR_Analysis_Claude/data/pending_approvals"
    
    # Email configuration (will be set via environment variables)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = os.getenv("CONSAR_EMAIL_USER")  # Set this in environment
    EMAIL_PASSWORD = os.getenv("CONSAR_EMAIL_PASSWORD")  # App password
    NOTIFY_EMAIL = os.getenv("CONSAR_NOTIFY_EMAIL", "louisvargas1148@gmail.com")
    
    # CONSAR summary URL to monitor for updates
    CONSAR_SUMMARY_URL = "https://www.consar.gob.mx/gobmx/aplicativo/siset/Enlace.aspx?md=79"
    
    # Monitoring settings
    CHECK_INTERVAL_HOURS = 24  # Daily check
    MAX_RETRY_ATTEMPTS = 3
    RETENTION_DAYS = 30  # Keep backups for 30 days

# === LOGGING SETUP ===
def setup_logging():
    """Configure logging for the monitor."""
    log_dir = Path("/Users/lvc/CONSAR_Analysis_Claude/logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "consar_monitor.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class ConsarMonitor:
    """Main monitoring class for CONSAR data updates."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.config = Config()
        self.state = self.load_monitor_state()
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories."""
        for path in [self.config.BACKUP_DIR, self.config.TEMP_DIR, 
                    self.config.PENDING_APPROVALS_DIR]:
            Path(path).mkdir(parents=True, exist_ok=True)
            
    def load_monitor_state(self):
        """Load monitoring state from file."""
        if Path(self.config.MONITOR_STATE_FILE).exists():
            with open(self.config.MONITOR_STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "last_check": None,
            "url_hashes": {},
            "last_data_update": None,
            "pending_approvals": []
        }
        
    def save_monitor_state(self):
        """Save monitoring state to file."""
        Path(self.config.MONITOR_STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.MONITOR_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def get_latest_periods(self):
        """Get latest available periods from CONSAR summary page."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(self.config.CONSAR_SUMMARY_URL, headers=headers, timeout=60)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all "periodo disponible" entries
                periods = set()
                
                # Look for table cells containing period information
                for cell in soup.find_all(['td', 'th']):
                    text = cell.get_text(strip=True)
                    # Look for patterns like "Ene 25-Jun 25" or "Feb 24-Jul 25"
                    if any(month in text for month in ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                                                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']):
                        # Extract period ranges like "Ene 25-Jun 25"
                        import re
                        matches = re.findall(r'(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)\s+(\d{2})', text)
                        for month, year in matches:
                            periods.add(f"{month} {year}")
                
                self.logger.info(f"Found periods: {sorted(periods)}")
                return periods
                
        except Exception as e:
            self.logger.error(f"Error getting latest periods: {e}")
        return set()
        
    def get_period_hash(self):
        """Get hash of available periods to detect new data."""
        periods = self.get_latest_periods()
        if periods:
            # Sort periods for consistent hashing
            period_string = "|".join(sorted(periods))
            return hashlib.md5(period_string.encode()).hexdigest()
        return None
        
    def check_for_updates(self):
        """Check CONSAR summary page for new data periods."""
        self.logger.info("Starting CONSAR update check...")
        
        try:
            # Get current available periods
            current_periods = self.get_latest_periods()
            current_hash = self.get_period_hash()
            
            if current_hash is None:
                self.logger.error("Could not get current period information")
                return []
                
            # Compare with stored hash
            stored_hash = self.state.get("period_hash")
            stored_periods = set(self.state.get("known_periods", []))
            
            if stored_hash != current_hash:
                # Find new periods
                new_periods = current_periods - stored_periods
                
                if new_periods:
                    self.logger.info(f"New periods detected: {sorted(new_periods)}")
                    updates_found = [{
                        "type": "new_periods",
                        "new_periods": sorted(new_periods),
                        "all_periods": sorted(current_periods),
                        "old_hash": stored_hash,
                        "new_hash": current_hash
                    }]
                else:
                    self.logger.info("Period hash changed but no new periods identified")
                    updates_found = []
                
                # Update stored state
                self.state["period_hash"] = current_hash
                self.state["known_periods"] = list(current_periods)
                
            else:
                self.logger.info("No new periods detected")
                updates_found = []
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            updates_found = []
                
        self.state["last_check"] = datetime.now().isoformat()
        self.save_monitor_state()
        
        return updates_found
        
    def create_database_backup(self):
        """Create timestamped backup of current database."""
        if not Path(self.config.CURRENT_DB_PATH).exists():
            self.logger.warning("Current database not found for backup")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"consar_db_backup_{timestamp}.json"
        backup_path = Path(self.config.BACKUP_DIR) / backup_name
        
        try:
            shutil.copy2(self.config.CURRENT_DB_PATH, backup_path)
            self.logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def cleanup_old_backups(self):
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.config.RETENTION_DAYS)
        backup_dir = Path(self.config.BACKUP_DIR)
        
        for backup_file in backup_dir.glob("consar_db_backup_*.json"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    backup_file.unlink()
                    self.logger.info(f"Removed old backup: {backup_file}")
                except Exception as e:
                    self.logger.error(f"Failed to remove old backup {backup_file}: {e}")
                    
    def run_processing_pipeline(self):
        """Execute the complete data processing pipeline."""
        self.logger.info("Starting data processing pipeline...")
        
        # Create temp directory for this run
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(self.config.TEMP_DIR) / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Download HTML files
            self.logger.info("Step 1: Downloading CONSAR HTML files...")
            result = subprocess.run([
                "python3", self.config.DOWNLOADER_PATH
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode != 0:
                raise Exception(f"Download failed: {result.stderr}")
                
            # Step 2: Process HTML to JSON
            self.logger.info("Step 2: Processing HTML files to JSON...")
            result = subprocess.run([
                "python3", self.config.PROCESSOR_PATH
            ], capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode != 0:
                raise Exception(f"Processing failed: {result.stderr}")
                
            # Step 3: Update FX rates
            self.logger.info("Step 3: Updating FX rates...")
            result = subprocess.run([
                "python3", self.config.FX_DOWNLOADER_PATH
            ], capture_output=True, text=True, timeout=300)  # 5 min timeout
            
            if result.returncode != 0:
                raise Exception(f"FX download failed: {result.stderr}")
                
            # Step 4: Convert to USD
            self.logger.info("Step 4: Converting to USD...")
            result = subprocess.run([
                "python3", self.config.USD_CONVERTER_PATH
            ], capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode != 0:
                raise Exception(f"USD conversion failed: {result.stderr}")
                
            self.logger.info("Processing pipeline completed successfully")
            return run_dir
            
        except Exception as e:
            self.logger.error(f"Processing pipeline failed: {e}")
            return None
            
    def extract_new_records(self, processed_output_path):
        """Extract only new records from processed data for approval."""
        # Load current database
        with open(self.config.CURRENT_DB_PATH, 'r') as f:
            current_db = json.load(f)
            
        # Load processed data (should be the output from USD converter)
        processed_data_path = "/Users/lvc/CascadeProjects/Afore_buy_sell_2.0/Historical_DB/consar_siefore_data_with_usd.json"
        
        if not Path(processed_data_path).exists():
            self.logger.error("Processed data file not found")
            return []
            
        with open(processed_data_path, 'r') as f:
            processed_data = json.load(f)
            
        # Create index of existing records
        existing_keys = set()
        for record in current_db:
            key = (
                record.get('Afore'),
                record.get('Siefore'), 
                record.get('Concept', record.get('Concept_Section')),
                record.get('PeriodYear'),
                record.get('PeriodMonth')
            )
            existing_keys.add(key)
            
        # Find new records
        new_records = []
        for record in processed_data:
            key = (
                record.get('Afore'),
                record.get('Siefore'),
                record.get('Concept', record.get('Concept_Section')),
                record.get('PeriodYear'),
                record.get('PeriodMonth')
            )
            
            if key not in existing_keys:
                new_records.append(record)
                
        self.logger.info(f"Found {len(new_records)} new records")
        return new_records
        
    def send_approval_email(self, new_records, run_id):
        """Send email with new records for human approval."""
        if not self.config.EMAIL_USER or not self.config.NOTIFY_EMAIL:
            self.logger.error("Email configuration missing")
            return False
            
        try:
            # Create approval package
            approval_id = f"approval_{run_id}"
            approval_dir = Path(self.config.PENDING_APPROVALS_DIR) / approval_id
            approval_dir.mkdir(exist_ok=True)
            
            # Save new records to file
            records_file = approval_dir / "new_records.json"
            with open(records_file, 'w') as f:
                json.dump(new_records, f, indent=2)
                
            # Create summary
            summary = self.create_records_summary(new_records)
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USER
            msg['To'] = self.config.NOTIFY_EMAIL
            msg['Subject'] = f"CONSAR Data Update Approval Required - {len(new_records)} new records"
            
            body = f"""
New CONSAR data has been processed and is ready for approval.

SUMMARY:
{summary}

APPROVAL COMMANDS:
To approve and merge these records:
  python3 consar_monitor.py --approve {approval_id}

To reject these records:
  python3 consar_monitor.py --reject {approval_id}

To review details:
  python3 consar_monitor.py --review {approval_id}

The new records are attached for your review.
Approval ID: {approval_id}
Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach new records file
            with open(records_file, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='json')
                attachment.add_header('Content-Disposition', 'attachment', 
                                    filename='new_records.json')
                msg.attach(attachment)
                
            # Send email
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_USER, self.config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            # Track pending approval
            self.state["pending_approvals"].append({
                "approval_id": approval_id,
                "created_at": datetime.now().isoformat(),
                "record_count": len(new_records),
                "status": "pending"
            })
            self.save_monitor_state()
            
            self.logger.info(f"Approval email sent for {approval_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send approval email: {e}")
            return False
            
    def create_records_summary(self, records):
        """Create human-readable summary of new records."""
        if not records:
            return "No new records found."
            
        # Group by period
        periods = {}
        for record in records:
            period = f"{record.get('PeriodYear')}-{record.get('PeriodMonth')}"
            if period not in periods:
                periods[period] = {"afores": set(), "concepts": set(), "count": 0}
            periods[period]["afores"].add(record.get("Afore"))
            periods[period]["concepts"].add(record.get("Concept", record.get("Concept_Section")))
            periods[period]["count"] += 1
            
        summary = f"Total new records: {len(records)}\\n\\n"
        
        for period, data in sorted(periods.items()):
            summary += f"Period {period}:\\n"
            summary += f"  - Records: {data['count']}\\n"
            summary += f"  - Afores: {', '.join(sorted(data['afores']))}\\n"
            summary += f"  - Concepts: {', '.join(sorted(data['concepts']))}\\n\\n"
            
        return summary
        
    def run_daily_check(self):
        """Main daily monitoring routine."""
        self.logger.info("Starting daily CONSAR monitoring check")
        
        try:
            # Clean up old backups
            self.cleanup_old_backups()
            
            # Check for updates
            updates = self.check_for_updates()
            
            if not updates:
                self.logger.info("No updates detected")
                return
                
            self.logger.info(f"Updates detected: {len(updates)} URLs changed")
            
            # Create backup before processing
            backup_path = self.create_database_backup()
            if not backup_path:
                self.logger.error("Failed to create backup - aborting")
                return
                
            # Run processing pipeline
            run_dir = self.run_processing_pipeline()
            if not run_dir:
                self.logger.error("Processing pipeline failed")
                return
                
            # Extract new records
            new_records = self.extract_new_records(run_dir)
            if not new_records:
                self.logger.info("No new records found after processing")
                return
                
            # Send approval email
            run_id = run_dir.name.replace("run_", "")
            if self.send_approval_email(new_records, run_id):
                self.logger.info("Approval email sent successfully")
                self.state["last_data_update"] = datetime.now().isoformat()
                self.save_monitor_state()
            else:
                self.logger.error("Failed to send approval email")
                
        except Exception as e:
            self.logger.error(f"Daily check failed: {e}")
            import traceback
            traceback.print_exc()
            
    def approve_records(self, approval_id):
        """Approve and merge pending records into main database."""
        self.logger.info(f"Processing approval for {approval_id}")
        
        approval_dir = Path(self.config.PENDING_APPROVALS_DIR) / approval_id
        if not approval_dir.exists():
            print(f"❌ Approval ID {approval_id} not found")
            return
            
        records_file = approval_dir / "new_records.json"
        if not records_file.exists():
            print(f"❌ Records file not found for {approval_id}")
            return
            
        try:
            # Load new records
            with open(records_file, 'r') as f:
                new_records = json.load(f)
                
            # Create backup before merge
            backup_path = self.create_database_backup()
            print(f"📋 Created backup: {backup_path}")
            
            # Load current database
            with open(self.config.CURRENT_DB_PATH, 'r') as f:
                current_db = json.load(f)
                
            # Merge records
            original_count = len(current_db)
            current_db.extend(new_records)
            
            # Save updated database
            with open(self.config.CURRENT_DB_PATH, 'w') as f:
                json.dump(current_db, f, indent=2)
                
            # Update approval status
            for approval in self.state["pending_approvals"]:
                if approval["approval_id"] == approval_id:
                    approval["status"] = "approved"
                    approval["approved_at"] = datetime.now().isoformat()
                    
            self.save_monitor_state()
            
            print(f"✅ Successfully merged {len(new_records)} new records")
            print(f"📊 Database updated: {original_count} → {len(current_db)} records")
            
            # Clean up approval files
            shutil.rmtree(approval_dir)
            print(f"🧹 Cleaned up approval files")
            
        except Exception as e:
            print(f"❌ Approval failed: {e}")
            self.logger.error(f"Approval failed for {approval_id}: {e}")
            
    def reject_records(self, approval_id):
        """Reject pending records."""
        self.logger.info(f"Processing rejection for {approval_id}")
        
        approval_dir = Path(self.config.PENDING_APPROVALS_DIR) / approval_id
        if not approval_dir.exists():
            print(f"❌ Approval ID {approval_id} not found")
            return
            
        try:
            # Update approval status
            for approval in self.state["pending_approvals"]:
                if approval["approval_id"] == approval_id:
                    approval["status"] = "rejected"
                    approval["rejected_at"] = datetime.now().isoformat()
                    
            self.save_monitor_state()
            
            # Clean up approval files
            shutil.rmtree(approval_dir)
            
            print(f"❌ Rejected approval {approval_id}")
            print(f"🧹 Cleaned up approval files")
            
        except Exception as e:
            print(f"❌ Rejection failed: {e}")
            self.logger.error(f"Rejection failed for {approval_id}: {e}")
            
    def review_records(self, approval_id):
        """Review pending records in detail."""
        approval_dir = Path(self.config.PENDING_APPROVALS_DIR) / approval_id
        if not approval_dir.exists():
            print(f"❌ Approval ID {approval_id} not found")
            return
            
        records_file = approval_dir / "new_records.json"
        if not records_file.exists():
            print(f"❌ Records file not found for {approval_id}")
            return
            
        try:
            with open(records_file, 'r') as f:
                new_records = json.load(f)
                
            print(f"📋 REVIEW: {approval_id}")
            print(f"📊 Total records: {len(new_records)}")
            print("="*80)
            
            # Show summary
            summary = self.create_records_summary(new_records)
            print(summary)
            
            # Show first 10 records in detail
            print("SAMPLE RECORDS (first 10):")
            print("-"*80)
            for i, record in enumerate(new_records[:10]):
                print(f"{i+1:2d}. {record.get('Afore'):12} | {record.get('Siefore'):15} | "
                      f"{record.get('Concept', record.get('Concept_Section', 'N/A')):25} | "
                      f"{record.get('PeriodYear')}-{record.get('PeriodMonth')} | "
                      f"${record.get('valueUSD', 0):,.0f}")
                      
            if len(new_records) > 10:
                print(f"... and {len(new_records) - 10} more records")
                
            print("="*80)
            print(f"To approve: python3 consar_monitor.py --approve {approval_id}")
            print(f"To reject:  python3 consar_monitor.py --reject {approval_id}")
            
        except Exception as e:
            print(f"❌ Review failed: {e}")
            self.logger.error(f"Review failed for {approval_id}: {e}")
            
    def list_pending_approvals(self):
        """List all pending approvals."""
        pending = [a for a in self.state.get("pending_approvals", []) 
                  if a.get("status") == "pending"]
                  
        if not pending:
            print("✅ No pending approvals")
            return
            
        print(f"📋 PENDING APPROVALS ({len(pending)})")
        print("="*80)
        
        for approval in pending:
            approval_id = approval["approval_id"]
            created = approval["created_at"]
            count = approval["record_count"]
            
            print(f"ID: {approval_id}")
            print(f"Created: {created}")
            print(f"Records: {count}")
            print(f"Review:  python3 consar_monitor.py --review {approval_id}")
            print(f"Approve: python3 consar_monitor.py --approve {approval_id}")
            print(f"Reject:  python3 consar_monitor.py --reject {approval_id}")
            print("-"*40)


def main():
    """Main entry point for the monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CONSAR Data Monitor')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run check once instead of continuous monitoring')
    parser.add_argument('--approve', type=str, 
                       help='Approve pending records by approval ID')
    parser.add_argument('--reject', type=str,
                       help='Reject pending records by approval ID') 
    parser.add_argument('--review', type=str,
                       help='Review pending records by approval ID')
    parser.add_argument('--list-pending', action='store_true',
                       help='List all pending approvals')
    
    args = parser.parse_args()
    
    monitor = ConsarMonitor()
    
    if args.approve:
        # Handle approval command
        monitor.approve_records(args.approve)
    elif args.reject:
        # Handle rejection command  
        monitor.reject_records(args.reject)
    elif args.review:
        # Handle review command
        monitor.review_records(args.review)
    elif args.list_pending:
        # List pending approvals
        monitor.list_pending_approvals()
    elif args.run_once:
        # Run single check
        monitor.run_daily_check()
    else:
        # Continuous monitoring mode
        print("Starting CONSAR monitor in continuous mode...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                monitor.run_daily_check()
                # Sleep for configured interval
                sleep_seconds = monitor.config.CHECK_INTERVAL_HOURS * 3600
                monitor.logger.info(f"Sleeping for {monitor.config.CHECK_INTERVAL_HOURS} hours...")
                time.sleep(sleep_seconds)
                
        except KeyboardInterrupt:
            print("\\nMonitor stopped by user")


if __name__ == "__main__":
    main()