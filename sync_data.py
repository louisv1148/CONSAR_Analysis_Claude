#!/usr/bin/env python3
"""
Automated Data Sync for CONSAR Analysis Project

This script:
1. Checks for updated data in the processing pipeline
2. Downloads/copies the latest database
3. Updates the analysis project
4. Optionally triggers new analysis
5. Can be run manually or via automation (cron/GitHub Actions)
"""

import json
import os
import shutil
import hashlib
import requests
from pathlib import Path
from datetime import datetime
import argparse

class DataSyncer:
    """Handles syncing data from processing pipeline to analysis project."""
    
    def __init__(self, config_file="sync_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def load_config(self):
        """Load sync configuration."""
        default_config = {
            "sources": {
                "local_processing": "/Users/lvc/CascadeProjects/Consar_report_processing/merged_consar_data_2019_2025.json",
                "github_release": "https://api.github.com/repos/louisv1148/Consar_report_processing/releases/latest"
            },
            "target_file": "data/merged_consar_data_2019_2025.json",
            "metadata_file": "data/data_metadata.json",
            "auto_analyze": True,
            "sync_log": "data/sync_log.json"
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
        else:
            config = default_config
            self.save_config(config)
            
        return config
        
    def save_config(self, config):
        """Save configuration to file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
    def get_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file."""
        if not Path(file_path).exists():
            return None
            
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
        
    def load_metadata(self):
        """Load existing data metadata."""
        metadata_file = Path(self.config["metadata_file"])
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
        
    def save_metadata(self, metadata):
        """Save data metadata."""
        metadata_file = Path(self.config["metadata_file"])
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
    def log_sync_event(self, event_type, message, success=True):
        """Log sync events."""
        log_file = Path(self.config["sync_log"])
        
        # Load existing log
        if log_file.exists():
            with open(log_file, 'r') as f:
                log = json.load(f)
        else:
            log = []
            
        # Add new event
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "success": success
        }
        log.append(event)
        
        # Keep only last 100 events
        log = log[-100:]
        
        # Save log
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
            
        print(f"[{event['timestamp']}] {event_type}: {message}")
        
    def check_local_source(self):
        """Check local processing pipeline for updates."""
        local_path = Path(self.config["sources"]["local_processing"])
        
        if not local_path.exists():
            return None, "Local source file not found"
            
        # Get file stats
        stat = local_path.stat()
        file_hash = self.get_file_hash(local_path)
        
        return {
            "source": "local",
            "path": str(local_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": file_hash
        }, "Local source available"
        
    def check_github_release(self):
        """Check GitHub releases for latest data."""
        try:
            api_url = self.config["sources"]["github_release"]
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                
                # Look for data assets
                for asset in release_data.get("assets", []):
                    if "merged_consar_data" in asset["name"].lower():
                        return {
                            "source": "github",
                            "download_url": asset["browser_download_url"],
                            "name": asset["name"],
                            "size": asset["size"],
                            "updated": asset["updated_at"],
                            "release_tag": release_data["tag_name"]
                        }, "GitHub release available"
                        
            return None, f"No data assets found in GitHub release (status: {response.status_code})"
            
        except requests.RequestException as e:
            return None, f"GitHub API error: {e}"
            
    def download_from_github(self, source_info):
        """Download data file from GitHub."""
        try:
            response = requests.get(source_info["download_url"], timeout=60)
            response.raise_for_status()
            
            temp_file = Path("data/temp_download.json")
            with open(temp_file, 'wb') as f:
                f.write(response.content)
                
            return str(temp_file), "Downloaded successfully"
            
        except requests.RequestException as e:
            return None, f"Download failed: {e}"
            
    def copy_from_local(self, source_info):
        """Copy data file from local source."""
        try:
            temp_file = Path("data/temp_local.json")
            shutil.copy2(source_info["path"], temp_file)
            return str(temp_file), "Copied successfully"
            
        except Exception as e:
            return None, f"Copy failed: {e}"
            
    def validate_data_file(self, file_path):
        """Validate the downloaded/copied data file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                return False, "Data is not a list"
                
            if len(data) == 0:
                return False, "Data is empty"
                
            # Check sample record structure
            sample = data[0]
            required_fields = ["Afore", "Siefore", "Concept", "valueMXN", "PeriodYear", "PeriodMonth"]
            missing_fields = [field for field in required_fields if field not in sample]
            
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"
                
            return True, f"Valid data file with {len(data):,} records"
            
        except json.JSONDecodeError:
            return False, "Invalid JSON format"
        except Exception as e:
            return False, f"Validation error: {e}"
            
    def sync_data(self, force=False):
        """Main sync process."""
        print("=== CONSAR Data Sync ===")
        
        # Load current metadata
        current_metadata = self.load_metadata()
        current_hash = current_metadata.get("hash")
        
        # Check available sources
        local_info, local_msg = self.check_local_source()
        github_info, github_msg = self.check_github_release()
        
        print(f"Local source: {local_msg}")
        print(f"GitHub source: {github_msg}")
        
        # Determine best source
        selected_source = None
        
        if local_info and github_info:
            # Compare timestamps and choose newer
            local_time = datetime.fromisoformat(local_info["modified"])
            github_time = datetime.fromisoformat(github_info["updated"])
            selected_source = local_info if local_time > github_time else github_info
        elif local_info:
            selected_source = local_info
        elif github_info:
            selected_source = github_info
        else:
            self.log_sync_event("ERROR", "No data sources available", False)
            return False
            
        # Check if update is needed
        if not force and selected_source.get("hash") == current_hash:
            self.log_sync_event("SKIP", "Data is already up to date")
            return True
            
        # Download/copy the data
        print(f"Syncing from {selected_source['source']} source...")
        
        if selected_source["source"] == "local":
            temp_file, result_msg = self.copy_from_local(selected_source)
        else:
            temp_file, result_msg = self.download_from_github(selected_source)
            
        if not temp_file:
            self.log_sync_event("ERROR", f"Failed to get data: {result_msg}", False)
            return False
            
        # Validate the data
        is_valid, validation_msg = self.validate_data_file(temp_file)
        if not is_valid:
            Path(temp_file).unlink(missing_ok=True)
            self.log_sync_event("ERROR", f"Data validation failed: {validation_msg}", False)
            return False
            
        # Move to final location
        target_file = Path(self.config["target_file"])
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(temp_file, target_file)
        
        # Update metadata
        new_hash = self.get_file_hash(target_file)
        new_metadata = {
            "last_sync": datetime.now().isoformat(),
            "source": selected_source["source"],
            "hash": new_hash,
            "file_size": target_file.stat().st_size,
            "validation": validation_msg
        }
        
        if selected_source["source"] == "github":
            new_metadata["github_release"] = selected_source["release_tag"]
            
        self.save_metadata(new_metadata)
        self.log_sync_event("SUCCESS", f"Data synced successfully: {validation_msg}")
        
        # Auto-analyze if configured
        if self.config.get("auto_analyze") and Path("generate_aum_table.py").exists():
            print("\nRunning automatic analysis...")
            os.system("python generate_aum_table.py")
            
        return True
        
    def status(self):
        """Show current sync status."""
        print("=== Data Sync Status ===")
        
        metadata = self.load_metadata()
        target_file = Path(self.config["target_file"])
        
        if target_file.exists():
            print(f"✅ Data file exists: {target_file}")
            print(f"   Size: {target_file.stat().st_size:,} bytes")
            print(f"   Modified: {datetime.fromtimestamp(target_file.stat().st_mtime)}")
        else:
            print(f"❌ Data file missing: {target_file}")
            
        if metadata:
            print(f"   Last sync: {metadata.get('last_sync', 'Never')}")
            print(f"   Source: {metadata.get('source', 'Unknown')}")
            print(f"   Validation: {metadata.get('validation', 'Not validated')}")
        else:
            print("   No sync metadata available")
            
        # Check sources
        local_info, local_msg = self.check_local_source()
        github_info, github_msg = self.check_github_release()
        
        print(f"\nSource availability:")
        print(f"   Local: {local_msg}")
        print(f"   GitHub: {github_msg}")

def main():
    parser = argparse.ArgumentParser(description='Sync CONSAR data from processing pipeline')
    parser.add_argument('--force', action='store_true', help='Force sync even if data appears current')
    parser.add_argument('--status', action='store_true', help='Show sync status')
    parser.add_argument('--config', type=str, default='sync_config.json', help='Configuration file path')
    
    args = parser.parse_args()
    
    syncer = DataSyncer(args.config)
    
    if args.status:
        syncer.status()
    else:
        syncer.sync_data(force=args.force)

if __name__ == "__main__":
    main()