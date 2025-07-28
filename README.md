# CONSAR Data Analysis

A comprehensive analysis tool for Mexican pension fund (CONSAR) data with plans for a web-based UI.

## Overview

This project provides analysis tools for CONSAR (Mexican pension system) data, including:
- AUM (Assets Under Management) analysis by pension fund company (Afore)
- Mutual fund investment analysis
- Historical trend analysis (2019-2025)
- Interactive data tables and visualizations

## Current Features

### 📊 AUM Analysis Table
Generate comprehensive AUM analysis tables showing:
- Total AUM by Afore (in USD)
- Mutual Fund AUM by Afore (in USD)
- Mutual Fund AUM as percentage of total AUM
- Industry totals and rankings

### 📈 Data Coverage
- **Time Period**: 2019 - 2025 (June)
- **Pension Funds**: 10 major Afores
- **Data Points**: 30,000+ records
- **Currency**: USD (converted from MXN using Banxico rates)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/louisv1148/consar-data-analysis.git
cd consar-data-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Generate AUM Analysis Table

```bash
# Latest period analysis
python generate_aum_table.py

# Specific period analysis
python generate_aum_table.py --period 2025-06

# Custom output file
python generate_aum_table.py --output my_analysis.csv
```

## Project Structure

```
consar-data-analysis/
├── README.md
├── requirements.txt
├── generate_aum_table.py      # Main analysis script
├── data/                      # Data directory
│   └── merged_consar_data_2019_2025.json
├── output/                    # Generated reports
│   └── *.csv
└── ui/                        # Future web UI (planned)
    ├── frontend/
    └── backend/
```

## Data Schema

Each record contains:
```json
{
  "Afore": "Pension fund company name",
  "Siefore": "Age-based pension category", 
  "Concept": "Financial concept (Total Assets, Mutual Funds, etc.)",
  "valueMXN": "Value in Mexican Pesos",
  "valueUSD": "Value in US Dollars",
  "FX_EOM": "End-of-month FX rate",
  "PeriodYear": "Year",
  "PeriodMonth": "Month"
}
```

## Supported Afores

- Azteca
- Banamex  
- Coppel
- Inbursa
- Invercap
- PensionISSSTE
- Principal
- Profuturo
- SURA
- XXI Banorte

## Roadmap

### Phase 1: Analysis Tools ✅
- [x] AUM analysis table generator
- [x] Historical data integration
- [x] CSV export functionality

### Phase 2: Web UI (Planned)
- [ ] React/Vue.js frontend
- [ ] Interactive charts and graphs
- [ ] Real-time data filtering
- [ ] Trend analysis visualizations
- [ ] Comparative analysis tools

### Phase 3: Advanced Features (Planned)
- [ ] Portfolio composition analysis
- [ ] Risk metrics calculation
- [ ] Automated report generation
- [ ] API for external integrations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Data Sources

- **CONSAR**: Mexican pension system official reports
- **Banxico**: Bank of Mexico FX rates
- **Processing Pipeline**: Automated HTML parsing and data standardization

## License

MIT License - See LICENSE file for details

## Contact

For questions or suggestions, please open an issue on GitHub.