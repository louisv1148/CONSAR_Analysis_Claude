from bs4 import BeautifulSoup

with open('/Users/lvc/CascadeProjects/Afore_buy_sell_2.0/downloaded_files/70-74_Reporte.html', 'r', encoding='latin-1') as f:
    soup = BeautifulSoup(f, 'html.parser')

rows = soup.find_all('tr')
print('=== FIRST 30 ROWS ===')
for i, row in enumerate(rows[:30]):
    cols = row.find_all('td')
    texts = [c.get_text(strip=True) for c in cols if c.get_text(strip=True)]
    if texts:
        first_text = texts[0]
        has_bold = any('font-weight:bold' in (c.get('style') or '').lower() for c in cols)
        print(f'Row {i:2d}: Bold={has_bold} | "{first_text[:60]}"')
        if any(word in first_text for word in ['Total de', 'Inversiones', 'Inversión']):
            print(f'      *** CONCEPT: "{first_text}"')