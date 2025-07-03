import pdfplumber
import pandas as pd
import os
import re

# Define the correct absolute path for the PDF file
pdf_path = os.path.abspath("E03394848_-_HC_997_-_Immigration_Rules_Changes__Web_Accessible_.pdf")

def split_amount_rate(value):
    """Split amount and rate from strings like '£88,100 (£45.18 per hour)'"""
    if not isinstance(value, str) or not value.strip():
        return value, ""
    
    # Pattern to match amount and rate
    pattern = r'(£[0-9,]+)\s*\((£[0-9.]+)\s*per\s*hour\)'
    match = re.search(pattern, value)
    
    if match:
        amount = match.group(1)
        rate = match.group(2)
        return amount, rate
    else:
        return value, ""

def extract_table_data(pdf_path, start_page, end_page, table_name, expected_cols, first_row_marker, last_row_marker):
    """Extract table data from specified page range"""
    all_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # For Table 2, let's first check what's on page 76 specifically
        if table_name == "Table 2":
            print(f"\n--- Checking page 76 specifically for Table 2 ---")
            page_76 = pdf.pages[75]  # 0-based indexing
            tables_76 = page_76.extract_tables()
            print(f"Found {len(tables_76)} tables on page 76")
            
            for idx, table in enumerate(tables_76):
                print(f"\nTable {idx} on page 76 has {len(table)} rows")
                for i, row in enumerate(table):
                    if row and row[0]:
                        first_col = str(row[0]).strip()
                        if "3556" in first_col or "Sales" in first_col:
                            print(f"Found potential target row {i}: {first_col}")
            
            # Also check raw text on page 76
            text_76 = page_76.extract_text()
            if "3556" in text_76:
                print("Found '3556' in raw text on page 76!")
                lines = text_76.split('\n')
                for i, line in enumerate(lines):
                    if "3556" in line:
                        print(f"Line {i}: {line}")
            else:
                print("'3556' not found in raw text on page 76")
        
        # Extract tables from the specified pages (convert to 0-based indexing)
        # For Table 2, extend the range to include page 77 to make sure we don't miss anything
        actual_end_page = end_page + 1 if table_name == "Table 2" else end_page
        
        for i in range(start_page - 1, actual_end_page):  # PDF pages are 1-indexed in requirements
            if i < len(pdf.pages):
                page = pdf.pages[i]
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        all_rows.extend(table)

    if not all_rows:
        print(f"No data found for {table_name}")
        return None

    # Find the start of actual data
    data_start_index = 0
    for i, row in enumerate(all_rows):
        if row and row[0]:
            first_col = str(row[0]).strip()
            if first_row_marker in first_col:
                data_start_index = i
                break
    
    # For Table 2, we need special handling to get all data up to the last row
    if table_name == "Table 2":
        print(f"\n--- Debugging Table 2 extraction ---")
        print(f"Looking for rows containing '3556' in all extracted rows...")
        
        # Search for any row containing "3556"
        found_3556_rows = []
        for i, row in enumerate(all_rows):
            if row and row[0]:
                first_col = str(row[0]).strip()
                if "3556" in first_col:
                    found_3556_rows.append((i, first_col))
                    print(f"Found 3556 at row {i}: {first_col}")
        
        if not found_3556_rows:
            print("No rows containing '3556' found! Checking all rows for Sales...")
            sales_rows = []
            for i, row in enumerate(all_rows):
                if row and row[0]:
                    first_col = str(row[0]).strip()
                    if "sales" in first_col.lower() or "Sales" in first_col:
                        sales_rows.append((i, first_col))
                        print(f"Found Sales at row {i}: {first_col}")
            
            # Look for the most likely candidate (highest numbered SOC code with Sales)
            for i, first_col in sales_rows:
                if any(digit in first_col for digit in "3456789"):  # Higher numbered SOC codes
                    print(f"Potential end candidate: Row {i}: {first_col}")
        
        # Print last 15 rows to see what we have
        print(f"\nLast 15 extracted rows:")
        for i, row in enumerate(all_rows[-15:]):
            actual_index = len(all_rows) - 15 + i
            first_col = str(row[0]).strip() if row and row[0] else "None"
            print(f"Row {actual_index}: {first_col}")
        
        # Find the end of actual data - look for the specific last row pattern
        data_end_index = len(all_rows)
        for i in range(data_start_index, len(all_rows)):
            if all_rows[i] and all_rows[i][0]:
                first_col = str(all_rows[i][0]).strip()
                # Look for the specific pattern "3556 Sales" or "3556"
                if "3556" in first_col and ("Sales" in first_col or "sales" in first_col.lower()):
                    data_end_index = i + 1  # Include this row
                    print(f"Found Table 2 end marker at row {i}: {first_col}")
                    break
        
        # If we didn't find the specific end marker, include all data from the page range
        if data_end_index == len(all_rows):
            print(f"End marker not found, using all available data for {table_name}")
    elif table_name == "Table 2aa":
        print(f"\n--- Debugging Table 2aa extraction ---")
        print(f"Looking for 3556 in Table 2aa range...")
        
        # Search for any row containing "3556"
        found_3556_rows = []
        for i, row in enumerate(all_rows):
            if row and row[0]:
                first_col = str(row[0]).strip()
                if "3556" in first_col:
                    found_3556_rows.append((i, first_col))
                    print(f"Found 3556 at row {i}: {first_col}")
        
        if not found_3556_rows:
            print("3556 not found in raw Table 2aa data!")
            print("Checking for 35xx codes around where 3556 should be...")
            
            # Look for 3555 and 3557 to see the pattern
            for i, row in enumerate(all_rows):
                if row and row[0]:
                    first_col = str(row[0]).strip()
                    if "3555" in first_col or "3557" in first_col:
                        print(f"Found {first_col} at row {i}")
                        # Print context around this row
                        for ctx in range(max(0, i-2), min(len(all_rows), i+3)):
                            ctx_row = all_rows[ctx]
                            ctx_col = str(ctx_row[0]).strip() if ctx_row and ctx_row[0] else "None"
                            marker = " <-- TARGET" if ctx == i else ""
                            print(f"  Row {ctx}: {ctx_col}{marker}")
        else:
            # Found 3556, let's examine it closely
            for row_idx, first_col in found_3556_rows:
                print(f"Found 3556 at row {row_idx}: {first_col}")
                full_row = all_rows[row_idx]
                print(f"Full row content (length: {len(full_row)}):")
                for col_idx, col_val in enumerate(full_row):
                    print(f"  Col {col_idx}: '{col_val}'")
                
                # Check if this row will pass our filters
                print(f"Filter checks:")
                print(f"  - Row exists: {bool(full_row)}")
                print(f"  - Has enough columns ({expected_cols}): {len(full_row) >= expected_cols}")
                print(f"  - First column not empty: {bool(full_row[0] if full_row else False)}")
                if full_row and full_row[0]:
                    first_clean = str(full_row[0]).strip()
                    print(f"  - First column clean: '{first_clean}'")
                    print(f"  - Matches 4-digit pattern: {bool(re.match(r'^\d{4}', first_clean))}")
                    # Show the regex match details
                    match = re.match(r'^\d{4}', first_clean)
                    if match:
                        print(f"    Matched: '{match.group()}'")
                    else:
                        print(f"    No match - first few chars: '{first_clean[:10]}'")
                print()
        
        # Find the end of actual data for Table 2aa
        data_end_index = len(all_rows)
        for i in range(data_start_index, len(all_rows)):
            if all_rows[i] and all_rows[i][0]:
                first_col = str(all_rows[i][0]).strip()
                if last_row_marker in first_col:
                    data_end_index = i + 1
                    break
    else:
        # For other tables, use the original logic
        data_end_index = len(all_rows)
        for i in range(data_start_index, len(all_rows)):
            if all_rows[i] and all_rows[i][0]:
                first_col = str(all_rows[i][0]).strip()
                if last_row_marker in first_col:
                    data_end_index = i + 1
                    break

    print(f"\n--- Processing {table_name} ---")
    print(f"Total rows found: {len(all_rows)}")
    print(f"Data start index: {data_start_index}")
    print(f"Data end index: {data_end_index}")
    
    # Extract data rows
    data_rows = all_rows[data_start_index:data_end_index]
    
    # Filter to keep only valid data rows
    filtered_rows = []
    skipped_rows = []  # Track skipped rows for debugging
    
    for row in data_rows:
        if row and len(row) >= expected_cols and row[0]:
            first_col = str(row[0]).strip()
            # Check if first column contains a 4-digit number (SOC code)
            if re.match(r'^\d{4}', first_col):
                filtered_rows.append(row)
            else:
                skipped_rows.append((first_col, "No 4-digit start"))
        else:
            if row:
                first_col = str(row[0]).strip() if row[0] else "None"
                if len(row) < expected_cols:
                    skipped_rows.append((first_col, f"Not enough cols: {len(row)} < {expected_cols}"))
                else:
                    skipped_rows.append((first_col, "Empty first column"))
    
    print(f"Filtered rows: {len(filtered_rows)}")
    
    # For Table 2aa, show skipped rows containing 3556
    if table_name == "Table 2aa":
        print(f"Skipped rows: {len(skipped_rows)}")
        for first_col, reason in skipped_rows:
            if "3556" in first_col:
                print(f"SKIPPED 3556 row: '{first_col}' - Reason: {reason}")
    
    # Debug: Print first and last few rows for Table 2
    if table_name == "Table 2" and filtered_rows:
        print(f"\nFirst 3 rows of {table_name}:")
        for i, row in enumerate(filtered_rows[:3]):
            print(f"Row {i}: {row[0] if row[0] else 'None'}")
        print(f"\nLast 5 rows of {table_name}:")
        for i, row in enumerate(filtered_rows[-5:]):
            print(f"Row {len(filtered_rows)-5+i}: {row[0] if row[0] else 'None'}")
    
    return filtered_rows

def process_table2_data(rows):
    """Process Table 2 data with special handling for col4-col7 splitting"""
    if not rows:
        return None
    
    # Header for Table 2 (will become 12 columns after splitting)
    header = [
        "SOC 2020 occupation code",
        "Equivalent SOC 2010 occupation code(s)", 
        "Examples of related job titles (non-exclusive)",
        "Going rate amount (SW – options F and I, GBM and SCU)",
        "Going rate per hour (SW – options F and I, GBM and SCU)",
        "90% going rate amount (SW – option G)",
        "90% going rate per hour (SW – option G)",
        "80% going rate amount (SW – option H)", 
        "80% going rate per hour (SW – option H)",
        "70% going rate amount (SW – option J, GTR)",
        "70% going rate per hour (SW – option J, GTR)",
        "Eligible for PhD points (SW)?"
    ]
    
    processed_rows = []
    for row in rows:
        if len(row) >= 8:
            new_row = []
            # Copy first 3 columns as-is, but preserve \n in col3
            new_row.append(str(row[0]).strip() if row[0] else "")
            new_row.append(str(row[1]).strip() if row[1] else "")
            # For col3, preserve \n characters
            new_row.append(str(row[2]) if row[2] else "")
            
            # Split col4-col7 (indices 3-6) into amount and rate pairs
            for i in range(3, 7):
                if i < len(row) and row[i]:
                    amount, rate = split_amount_rate(str(row[i]))
                    new_row.append(amount)
                    new_row.append(rate)
                else:
                    new_row.append("")
                    new_row.append("")
            
            # Add the last column (col8)
            new_row.append(str(row[7]).strip() if len(row) > 7 and row[7] else "")
            
            processed_rows.append(new_row)
    
    df = pd.DataFrame(processed_rows, columns=header)
    return df

def process_other_table_data(rows, table_name, expected_cols):
    """Process other table data (Table 2aa, 2a, 2b, 3a)"""
    if not rows:
        return None
    
    # Define headers based on table type
    if table_name in ["Table 2aa"]:
        # 8 columns like Table 2
        header = [
            "SOC 2020 occupation code",
            "Equivalent SOC 2010 occupation code(s)",
            "Examples of related job titles (non-exclusive)", 
            "Going rate (SW – options F and I, GBM and SCU)",
            "90% of going rate (SW – option G)",
            "80% of going rate (SW – option H)",
            "70% of going rate (SW – option J, GTR)",
            "Eligible for PhD points (SW)?"
        ]
    elif table_name in ["Table 2a", "Table 2b"]:
        # 6 columns
        header = [
            "SOC 2020 occupation code",
            "Equivalent SOC 2010 occupation code(s)",
            "Examples of related job titles (non-exclusive)",
            "Going rate per hour",
            "New entrant rate per hour",
            "Additional column"
        ]
    elif table_name == "Table 3a":
        # 5 columns
        header = [
            "SOC 2020 occupation code", 
            "Equivalent SOC 2010 occupation code(s)",
            "Examples of related job titles (non-exclusive)",
            "Going rate per hour",
            "New entrant rate per hour"
        ]
    else:
        # Generic header based on expected columns
        header = [f"Column_{i+1}" for i in range(expected_cols)]
    
    # Ensure all rows have the expected number of columns
    processed_rows = []
    for row in rows:
        new_row = []
        for i in range(len(header)):
            if i < len(row) and row[i]:
                new_row.append(str(row[i]).strip())
            else:
                new_row.append("")
        processed_rows.append(new_row)
    
    df = pd.DataFrame(processed_rows, columns=header)
    return df

def extract_all_tables(pdf_path, output_filename):
    """Extract all required tables and save to Excel with multiple sheets"""
    
    # Table definitions based on requirements
    tables_config = [
        {
            "name": "Table 2",
            "start_page": 56,
            "end_page": 80,  # Extended to include page 80 where 3556 is located
            "expected_cols": 8,
            "first_row": "1111 Chief",
            "last_row": "3556 Sales"
        },
        {
            "name": "Table 2aa",
            "start_page": 81,  # Start after Table 2 ends
            "end_page": 112,
            "expected_cols": 8, 
            "first_row": "1150 Managers",
            "last_row": "9249 Elementary"
        },
        {
            "name": "Table 2a",
            "start_page": 113,
            "end_page": 114,
            "expected_cols": 6,
            "first_row": "3214",
            "last_row": "9252"
        },
        {
            "name": "Table 2b", 
            "start_page": 115,
            "end_page": 118,
            "expected_cols": 6,
            "first_row": "1232",
            "last_row": "3543 Project"
        },
        {
            "name": "Table 3a",
            "start_page": 119,
            "end_page": 121, 
            "expected_cols": 5,
            "first_row": "3213 Medical",
            "last_row": "6133 Dental"
        }
    ]
    
    # Create Excel writer object
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        
        for table_config in tables_config:
            print(f"\n{'='*50}")
            print(f"Extracting {table_config['name']}")
            print(f"{'='*50}")
            
            # Extract raw table data
            rows = extract_table_data(
                pdf_path,
                table_config["start_page"],
                table_config["end_page"], 
                table_config["name"],
                table_config["expected_cols"],
                table_config["first_row"],
                table_config["last_row"]
            )
            
            if rows:
                # Process data based on table type
                if table_config["name"] == "Table 2":
                    df = process_table2_data(rows)
                else:
                    df = process_other_table_data(rows, table_config["name"], table_config["expected_cols"])
                
                if df is not None and not df.empty:
                    # Clean the data
                    df = df.dropna(how='all')
                    
                    # Save to Excel sheet
                    sheet_name = table_config["name"]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"{table_config['name']} extracted successfully: {len(df)} rows")
                else:
                    print(f"No valid data found for {table_config['name']}")
            else:
                print(f"Could not extract {table_config['name']}")
    
    print(f"\nAll tables have been extracted and saved to {output_filename}")

def search_3556_in_pdf(pdf_path):
    """Search for '3556' throughout the entire PDF to find where it is located"""
    print(f"\n--- Searching entire PDF for '3556' ---")
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages in PDF: {total_pages}")
        
        found_pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and "3556" in text:
                found_pages.append(i + 1)  # Convert to 1-based page numbering
                print(f"Found '3556' on page {i + 1}")
                
                # Extract the relevant lines
                lines = text.split('\n')
                for line_num, line in enumerate(lines):
                    if "3556" in line:
                        print(f"  Line {line_num}: {line.strip()}")
                        # Print some context lines
                        for context in range(max(0, line_num-2), min(len(lines), line_num+3)):
                            if context != line_num:
                                print(f"  Context {context}: {lines[context].strip()}")
                print()
        
        if not found_pages:
            print("No pages containing '3556' found in the entire PDF!")
            # Let's also search for variations
            print("Searching for 'Sales' in pages 70-80...")
            for i in range(69, min(80, total_pages)):  # Pages 70-80
                page = pdf.pages[i]
                text = page.extract_text()
                if text and "Sales" in text:
                    print(f"Found 'Sales' on page {i + 1}")
        else:
            print(f"Found '3556' on pages: {found_pages}")
    
    return found_pages

# Main execution
if __name__ == "__main__":
    if not os.path.exists(pdf_path):
        print(f"Error: The file {pdf_path} was not found.")
    else:
        # First, search for '3556' throughout the PDF
        found_pages = search_3556_in_pdf(pdf_path)
        
        # Extract all tables
        extract_all_tables(pdf_path, "table_2_and_related_data.xlsx") 