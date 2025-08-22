#!/usr/bin/env python3
"""
Trigger Sync from Processing Pipeline

This script should be called from the processing pipeline when new data is available.
It will trigger the analysis project to sync the latest data.
"""

import requests
import json
import os
from datetime import datetime

def trigger_github_sync(github_token, repo_owner="louisv1148", repo_name="consar-data-analysis"):
    """Trigger GitHub Action via repository dispatch."""
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "event_type": "data-updated",
        "client_payload": {
            "timestamp": datetime.now().isoformat(),
            "source": "processing-pipeline",
            "message": "New CONSAR data available"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"✅ Successfully triggered sync in {repo_owner}/{repo_name}")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Failed to trigger sync: {e}")
        return False

def main():
    # Get GitHub token from environment variable
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("   Please set it with: export GITHUB_TOKEN=your_token_here")
        return False
        
    print("🔄 Triggering data sync in analysis project...")
    return trigger_github_sync(github_token)

if __name__ == "__main__":
    main()