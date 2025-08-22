# CONSAR Data Analysis Web App

A Streamlit-based web application for generating CONSAR analysis tables with interactive features.

## Features

### 📊 Table Types
- **Basic AUM Analysis**: Total AUM and Mutual Fund AUM breakdown by Afore
- **Professional Tables**: Detailed AUM analysis in USD millions
- **Third Party Mandates**: Analysis of third-party managed assets
- **Total Active Management**: Combined mutual funds and third-party mandates

### 💱 Currency Options
- **USD**: Analysis in US Dollars
- **MXN**: Analysis in Mexican Pesos
- **Both**: Side-by-side USD and MXN analysis

### 📅 Date Selection
- Choose from any available period in the database (2019-02 to 2025-06)
- Automatically handles data availability per period

### 📥 Export Options
- **Excel**: Download tables as .xlsx files
- **CSV**: Download tables as .csv files
- Individual download links for each table

## Quick Start

### 1. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install app requirements
pip install -r requirements_app.txt
```

### 2. Run the App
```bash
streamlit run consar_app.py
```

### 3. Access the App
Open your browser and go to: `http://localhost:8501`

## Usage Guide

### Step 1: Configure Analysis Settings
1. **Select Analysis Period**: Choose from available periods in the dropdown
2. **Choose Currency**: Select USD, MXN, or Both
3. **Select Tables**: Pick which analysis tables to generate
4. **Export Format**: Choose Excel or CSV for downloads

### Step 2: Generate Analysis
1. Click the "🚀 Generate Analysis" button
2. View results in interactive tables
3. Use expanders to show/hide different sections

### Step 3: Export Data
1. Use the download links below each table
2. Files are named automatically with period information
3. Excel files include formatted sheets with proper headers

## App Structure

```
consar_app.py               # Main Streamlit application
├── Sidebar Controls        # Period, currency, table selection
├── Main Display Area       # Generated tables and metrics
├── Export Functions        # CSV and Excel download links
└── Data Overview          # Database statistics when idle
```

## Technical Features

### Caching
- Data loading is cached for better performance
- Available periods are cached to avoid recalculation

### Error Handling
- Graceful handling of missing data periods
- User-friendly error messages
- Exception handling for data processing

### Responsive Design
- Mobile-friendly layout
- Expandable sections for better organization
- Professional styling with custom CSS

## Data Requirements

### Database File
- Location: `data/merged_consar_data_2019_2025.json`
- Must contain proper period and FX rate information
- Supports both MXN and USD value fields

### Expected Data Fields
```json
{
  "Afore": "Afore name",
  "Concept": "Investment concept",
  "valueMXN": 123456.78,
  "valueUSD": 6789.01,
  "PeriodYear": "2024",
  "PeriodMonth": "12",
  "FX_EOM": 20.7862
}
```

## Troubleshooting

### Common Issues

**App won't start**
- Ensure all dependencies are installed
- Check that the database file exists
- Verify Python virtual environment is activated

**No data for selected period**
- Check available periods in the data overview
- Verify the database contains data for that period
- Some periods may only have MXN data, not USD

**Export not working**
- Ensure openpyxl is installed for Excel exports
- Check browser download permissions
- Try refreshing the page and regenerating

### Performance Tips
- Use caching by not changing periods frequently
- Select only needed tables to reduce processing time
- For large datasets, consider using CSV exports over Excel

## Support

For issues or feature requests, please check the main project documentation or contact the development team.