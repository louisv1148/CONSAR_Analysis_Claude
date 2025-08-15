import os
import json
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

# === CONFIG ===
HTML_FOLDER = "/Users/lvc/CascadeProjects/Afore_buy_sell_2.0/downloaded_files"
JSON_DB_PATH = "/Users/lvc/CascadeProjects/Afore_buy_sell_2.0/Historical_DB/consar_siefore_data.json"

# === LOAD EXISTING DATA ===
if not os.path.exists(os.path.dirname(JSON_DB_PATH)):
    os.makedirs(os.path.dirname(JSON_DB_PATH))

if os.path.exists(JSON_DB_PATH):
    try:
        with open(JSON_DB_PATH, "r", encoding="utf-8") as f:
            database = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {JSON_DB_PATH} is empty or not valid JSON. Starting with an empty database.")
        database = []
else:
    print(f"No existing database found at {JSON_DB_PATH}. Starting with an empty database.")
    database = []

# === INDEX EXISTING RECORDS FOR DEDUPLICATION ===
existing_keys = set()
if isinstance(database, list):
    try:
        existing_keys = {
            (d["Afore"], d["Siefore"], d.get("Concept", ""), d["PeriodYear"], d["PeriodMonth"])
            for d in database if isinstance(d, dict)
        }
    except (TypeError, KeyError) as e:
        print(f"Error with existing database keys: {e}. Starting fresh.")
        database = []
        existing_keys = set()

# === HELPER: Normalize period to Year-Month ===
def normalize_period(period_text):
    month_map_es = {
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12',
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04', 'Mayo': '05', 'Junio': '06',
        'Julio': '07', 'Agosto': '08', 'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
    }
    period_text = period_text.strip()

    # Extract month and year from formats like "Mar-2025", "Abr-25", etc.
    for month_es, month_num_str in month_map_es.items():
        match = re.search(r"(?i)\b" + re.escape(month_es) + r"\b(?:[ -\.]*de[ -\.]*|[ -\.]*)(\d{4}|\d{2})\b", period_text)
        if match:
            year_str = match.group(1)
            year = int(year_str)
            if year < 100:  # Handle YY format
                current_century = (datetime.now().year // 100) * 100
                year += current_century
            return str(year), month_num_str

    # Fallback for "MM/YYYY"
    try:
        dt = datetime.strptime(period_text, "%m/%Y")
        return dt.strftime("%Y"), dt.strftime("%m")
    except ValueError:
        pass
    
    # Additional fallbacks
    for fmt in ("%b-%Y", "%b-%y"):
        try:
            dt = datetime.strptime(period_text, fmt)
            return dt.strftime("%Y"), dt.strftime("%m")
        except ValueError:
            continue

    return None, None

# === PARSE HTML FILE ===
def parse_html_file(filepath, siefore_name):
    with open(filepath, "r", encoding="latin-1") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = soup.find_all("tr")
    records = []
    periods = []
    current_concept = None

    for row_idx, row in enumerate(rows):
        cols = row.find_all("td")
        raw_cell_texts = [c.get_text(strip=True) for c in cols]
        cell_styles = [c.get('style') for c in cols]
        texts = [t for t in raw_cell_texts if t]

        if not texts:
            continue

        # Skip header section with siefore title
        if "Estado de Situación Financiera" in texts[0]:
            continue

        # Look for period headers (May-2025, Jun-2025, etc.)
        if any(re.search(r'\b(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)[-\s]*\d{2,4}\b', text, re.IGNORECASE) for text in texts):
            periods = [text for text in texts if re.search(r'\b(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic|Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)[-\s]*\d{2,4}\b', text, re.IGNORECASE)]
            print(f"    PERIOD HEADER FOUND: {periods}")
            continue

        if not periods:
            continue

        # Identify concepts (bold rows with financial concepts)
        first_cell_text = texts[0]
        has_bold = any('font-weight:bold' in (col.get('style') or '').lower() for col in cols)
        
        if (len(texts) == len(periods) + 1 and has_bold and 
            any(word in first_cell_text for word in ['Total de', 'Inversiones', 'Inversión'])):
            current_concept = first_cell_text.strip()
            print(f"    CONCEPT FOUND: {current_concept}")
            continue

        # Skip if we don't have a concept or proper number of columns
        if not current_concept or len(texts) < len(periods) + 1:
            continue

        # Extract Afore name and values
        afore_name = texts[0].strip()
        values = texts[1:]

        # Process each period's value
        for i, val_str in enumerate(values):
            if i >= len(periods):
                break
            
            try:
                cleaned_val = val_str.replace(",", "").strip()
                if not cleaned_val or cleaned_val.lower() == 'n/d' or cleaned_val == '-':
                    continue
                value_mxn = float(cleaned_val)
            except ValueError:
                continue

            year, month = normalize_period(periods[i])
            if not year:
                continue

            key = (afore_name, siefore_name, current_concept, year, month)
            if key in existing_keys:
                continue

            records.append({
                "Afore": afore_name,
                "Siefore": siefore_name,
                "Concept": current_concept,
                "valueMXN": value_mxn,
                "PeriodYear": year,
                "PeriodMonth": month
            })
            existing_keys.add(key)

    return records

# === PROCESS ALL HTML FILES ===
print(f"Starting processing of HTML files from: {os.path.abspath(HTML_FOLDER)}")
newly_added_records_count = 0

if not os.path.exists(HTML_FOLDER):
    print(f"ERROR: HTML_FOLDER does not exist: {os.path.abspath(HTML_FOLDER)}")
else:
    for filename in os.listdir(HTML_FOLDER):
        if filename.endswith(".html"):
            siefore_name = filename.replace("_Reporte.html", "")
            filepath = os.path.join(HTML_FOLDER, filename)
            try:
                new_records = parse_html_file(filepath, siefore_name)
                if new_records:
                    database.extend(new_records)
                    newly_added_records_count += len(new_records)
                    print(f"  Added {len(new_records)} new records from {filename}.")
                else:
                    print(f"  No new records found or added from {filename}.")
            except Exception as e:
                print(f"  ERROR processing file {filename}: {e}")
                import traceback
                traceback.print_exc()

# === SAVE UPDATED DB ===
with open(JSON_DB_PATH, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

print(f"Processing complete. Total records in database: {len(database)}.")
print(f"{newly_added_records_count} new records were added in this run.")