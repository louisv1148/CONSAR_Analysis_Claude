# CONSAR Data Pipeline Setup

This document explains how the automated data pipeline works between the processing and analysis projects.

## 🏗️ **Architecture Overview**

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Data Processing   │    │   Analysis Project   │    │     GitHub          │
│                     │    │                      │    │                     │
│ 1. Download HTML    │    │ 1. Sync latest data  │    │ 1. Store releases   │
│ 2. Parse & Convert  │────▶ 2. Generate tables   │────▶ 2. Trigger actions  │
│ 3. Merge historical │    │ 3. Update analysis   │    │ 3. Host results     │
│ 4. Notify analysis  │    │ 4. Commit results    │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## 🔄 **Data Flow**

### **Step 1: Data Processing** (Consar_report_processing)
1. `afore_downloader.py` downloads HTML files
2. `process_consar_reports_improved.py` processes HTML → JSON
3. `merge_with_historical.py` merges with historical data
4. `notify_analysis_project.py` triggers analysis update

### **Step 2: Data Analysis** (consar-data-analysis)
1. `sync_data.py` detects new data and syncs
2. `generate_aum_table.py` creates analysis tables
3. Results committed to GitHub automatically

### **Step 3: Automation** (GitHub Actions)
1. Daily scheduled sync at 9 AM UTC
2. Manual trigger available
3. Webhook trigger from processing pipeline
4. Automated releases with data snapshots

## 📁 **File Structure**

### Analysis Project (`consar-data-analysis/`)
```
├── README.md                          # Project documentation
├── PIPELINE_SETUP.md                  # This file
├── requirements.txt                   # Python dependencies
├── sync_data.py                       # Main sync script
├── generate_aum_table.py              # Analysis generator
├── trigger_sync.py                    # GitHub webhook trigger
├── sync_config.json                   # Auto-generated config
├── data/                              # Data directory
│   ├── merged_consar_data_2019_2025.json  # Main database
│   ├── data_metadata.json             # Sync metadata
│   └── sync_log.json                  # Sync history
├── output/                            # Generated analysis
│   └── consar_aum_analysis_*.csv      # Analysis tables
├── .github/workflows/                 # GitHub Actions
│   └── sync-data.yml                  # Automated sync workflow
└── ui/                                # Future web UI
    ├── frontend/
    └── backend/
```

### Processing Project (`Consar_report_processing/`)
```
├── process_consar_reports_improved.py  # Main processor
├── merge_with_historical.py           # Data merger
├── notify_analysis_project.py         # Analysis trigger
├── test_output.json                   # Latest processed data
└── merged_consar_data_2019_2025.json  # Merged database
```

## 🚀 **Setup Instructions**

### **1. Initial Setup**

```bash
# Clone the analysis project
git clone https://github.com/louisv1148/consar-data-analysis.git
cd consar-data-analysis

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run initial sync
python sync_data.py
```

### **2. Configure Processing Pipeline**

Add this to the end of your processing scripts:

```python
# At the end of merge_with_historical.py
if __name__ == "__main__":
    merger = DataMerger(args.new_data, args.historical_db, args.output)
    result = merger.run()
    
    # Notify analysis project
    if result:
        os.system("python notify_analysis_project.py")
```

### **3. GitHub Integration** (Optional)

```bash
# Set up GitHub token for API access
export GITHUB_TOKEN=your_github_token_here

# Test webhook trigger
python trigger_sync.py
```

## 🔧 **Usage Examples**

### **Manual Sync**
```bash
# Check sync status
python sync_data.py --status

# Force sync (ignore timestamp checks)
python sync_data.py --force

# Generate latest analysis
python generate_aum_table.py

# Generate analysis for specific period
python generate_aum_table.py --period 2025-05
```

### **Automated Pipeline**

The complete pipeline runs automatically when:

1. **Daily Schedule**: 9 AM UTC via GitHub Actions
2. **Manual Trigger**: GitHub Actions can be triggered manually
3. **Processing Complete**: When processing pipeline finishes
4. **Webhook**: Via repository dispatch events

## 📊 **Output Examples**

### **AUM Analysis Table**
```
CONSAR AUM ANALYSIS - PERIOD: 2025-06
================================================================================
Afore         Total AUM (USD) Mutual Fund AUM (USD) MF AUM as % of Total
Azteca        $19,201,702     $752,712              3.92%
Banamex       $66,028,638     $0                    0.00%
SURA          $68,183,571     $2,031,673            2.98%
TOTAL         $406,194,743    $4,260,016            1.05%
================================================================================
```

### **CSV Output**
- Saved to `output/consar_aum_analysis_YYYY_MM.csv`
- Machine-readable format for further analysis
- Includes precise numeric values (not formatted)

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **"Local source file not found"**
   ```bash
   # Check if processing pipeline path is correct
   python sync_data.py --status
   
   # Update config if needed
   nano sync_config.json
   ```

2. **"GitHub API error"**
   ```bash
   # Set up GitHub token
   export GITHUB_TOKEN=your_token_here
   
   # Or disable GitHub sync in config
   ```

3. **"Data validation failed"**
   ```bash
   # Check data file integrity
   python -c "import json; json.load(open('data/merged_consar_data_2019_2025.json'))"
   
   # Force re-sync
   python sync_data.py --force
   ```

### **Logs and Monitoring**

- **Sync Log**: `data/sync_log.json` - Last 100 sync events
- **GitHub Actions**: Check workflow runs in GitHub repository
- **Local Logs**: Console output from sync commands

## 🔮 **Future Enhancements**

1. **Real-time Sync**: WebSocket connections for instant updates
2. **Web Dashboard**: Monitor pipeline status via web UI
3. **Email Notifications**: Alert on sync failures
4. **Data Versioning**: Track database changes over time
5. **API Endpoints**: Programmatic access to latest data

## 📞 **Support**

For issues with the data pipeline:
1. Check the troubleshooting section above
2. Review sync logs in `data/sync_log.json`
3. Open an issue on GitHub with detailed logs
4. Include sync status output: `python sync_data.py --status`