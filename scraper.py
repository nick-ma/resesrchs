
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys

# URL of the page
url = "https://www.gov.uk/government/publications/skilled-worker-visa-eligible-occupations/skilled-worker-visa-eligible-occupations-and-codes"

# Fetch the page content
print("Fetching page content...")
response = requests.get(url)
response.raise_for_status()

# Parse the HTML
soup = BeautifulSoup(response.content, "html.parser")

# Find all tables and identify the main one by size (most rows)
all_tables = soup.find_all("table")
if not all_tables:
    print("Error: No tables found on the page.")
    sys.exit(1)

main_table = max(all_tables, key=lambda table: len(table.find_all('tr')))

if not main_table:
    print("Error: Could not identify the main table.")
    sys.exit(1)

# Extract headers from the <thead> section
thead = main_table.find('thead')
if not thead:
    print("Error: Table has no <thead> section.")
    sys.exit(1)

headers = [th.get_text(strip=True) for th in thead.find_all('th')]
print(f"Found headers: {headers}")

# Find the index of the "Related job titles" column to handle <br> tags
try:
    job_titles_index = headers.index("Related job titles")
except ValueError:
    job_titles_index = -1 # Column not found

# Extract data rows from the <tbody> section
tbody = main_table.find('tbody')
if not tbody:
    print("Error: Table has no <tbody> section.")
    sys.exit(1)

rows_data = []
for row in tbody.find_all('tr'):
    # Find all cell types ('th' and 'td') within the row to capture all data.
    all_cells = row.find_all(['th', 'td'])
    
    cell_texts = []
    for i, cell in enumerate(all_cells):
        # If this is the "Related job titles" column, process it specially.
        if i == job_titles_index:
            # Replace <br> tags with newline characters
            for br in cell.find_all("br"):
                br.replace_with("\n")
            
            # Get the full text block from the cell
            raw_text = cell.get_text()
            
            # Split the block into individual lines, strip whitespace from each,
            # filter out any empty lines, and then join them back together.
            lines = raw_text.split('\n')
            stripped_lines = [line.strip() for line in lines]
            non_empty_lines = [line for line in stripped_lines if line]
            final_text = '\n'.join(non_empty_lines)
            
            cell_texts.append(final_text)
        else:
            cell_texts.append(cell.get_text(strip=True))

    if len(cell_texts) == len(headers):
        rows_data.append(cell_texts)

if not rows_data:
    print("Warning: Found 0 data rows in the table body.")
else:
    print(f"Successfully extracted {len(rows_data)} rows.")

# Create a pandas DataFrame
df = pd.DataFrame(rows_data, columns=headers)

# --- SAVE TO EXCEL WITH WRAPPING ---
output_file = "eligible_occupations.xlsx"
print(f"Saving data to {output_file} with text wrapping...")

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
df.to_excel(writer, index=False, sheet_name='Eligible Occupations')

# Get the xlsxwriter workbook and worksheet objects.
workbook  = writer.book
worksheet = writer.sheets['Eligible Occupations']

# Add a new format for text wrapping.
wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})

# Set column widths and apply the wrap format to the 'Related job titles' column
worksheet.set_column('A:A', 15) # Occupation code
worksheet.set_column('B:B', 30) # Job type
worksheet.set_column('D:D', 20) # Eligible for Skilled Worker

if job_titles_index != -1:
    # Convert column index to Excel's letter format (e.g., 0 -> A, 1 -> B)
    col_letter = chr(ord('A') + job_titles_index)
    worksheet.set_column(f'{col_letter}:{col_letter}', 50, wrap_format)

# Close the Pandas Excel writer and output the Excel file.
writer.close()

print("Successfully saved the file.")

