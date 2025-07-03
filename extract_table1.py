import pdfplumber
import pandas as pd
import os
import re

# Define the correct absolute path for the PDF file
pdf_path = os.path.abspath("E03394848_-_HC_997_-_Immigration_Rules_Changes__Web_Accessible_.pdf")

def split_salary_data(salary_str):
    """
    Split salary data like '£88,100 (£45.18 per hour)' into amount and rate
    Returns (amount, rate) tuple
    """
    if not salary_str or pd.isna(salary_str):
        return None, None
    
    salary_str = str(salary_str).strip()
    if not salary_str or salary_str in ['Not applicable', '']:
        return salary_str, None
    
    # Extract amount (£XX,XXX)
    amount_match = re.search(r'£[\d,]+', salary_str)
    amount = amount_match.group() if amount_match else None
    
    # Extract rate (£XX.XX per hour)
    rate_match = re.search(r'£[\d.]+(?=\s*per\s*hour)', salary_str)
    rate = rate_match.group() if rate_match else None
    
    return amount, rate

def extract_table_data(pdf_path, start_page, end_page, table_name, first_row_pattern, last_row_pattern):
    """
    Extract table data from specified page range
    """
    all_rows = []
    
    print(f"Extracting {table_name} from pages {start_page + 1} to {end_page}")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract tables from the specified pages
        for i in range(start_page, end_page):
            if i < len(pdf.pages):
                page = pdf.pages[i]
                tables = page.extract_tables()
                for table in tables:
                    all_rows.extend(table)

    if not all_rows:
        print(f"No data found for {table_name}")
        return pd.DataFrame()

    # Find the start of the actual data
    data_start_index = 0
    for i, row in enumerate(all_rows):
        if row and len(row) >= 1 and row[0] and str(row[0]).strip():
            if re.search(first_row_pattern, str(row[0])):
                data_start_index = i
                print(f"Found first row at index {i}: {row[0]}")
                break

    print(f"Data start index for {table_name}: {data_start_index}")
    
    # Process and standardize rows
    processed_rows = []
    expected_cols = 7  # Original 7 columns
    
    found_last_row = False
    for idx, row in enumerate(all_rows[data_start_index:]):
        # Skip empty rows
        if not row or not any(row):
            continue
        
        # Skip header rows
        if row[0] and ('SOC 2020 occupation code' in str(row[0]) or 'Examples of related' in str(row[0])):
            continue
            
        # Only process rows that start with a 4-digit SOC code
        if not (row[0] and re.match(r'^\d{4}', str(row[0]).strip())):
            continue
        
        # Standardize row length first
        if len(row) >= expected_cols:
            current_row = row[:expected_cols]
        else:
            # Pad with None if too short
            current_row = row + [None] * (expected_cols - len(row))
            
        processed_rows.append(current_row)
        
        # Check if we've reached the last row AFTER adding it
        if re.search(last_row_pattern, str(row[0])):
            found_last_row = True
            print(f"Found last row at processed index {len(processed_rows)}: {row[0]}")
            break

    print(f"Processed {len(processed_rows)} rows for {table_name}")
    print(f"Found last row pattern: {found_last_row}")
    
    if not processed_rows:
        print(f"No valid data rows found for {table_name}")
        return pd.DataFrame()

    # Define original column names
    original_columns = [
        "SOC 2020 occupation code",
        "Examples of related job titles (non-exclusive)",
        "Going rate (SW – options A and D)",
        "90% of going rate (SW – option B)",
        "80% of going rate (SW – option C)",
        "70% of going rate (SW – option E)",
        "Eligible for PhD points (SW)?",
    ]
    
    # Create DataFrame with original columns
    df = pd.DataFrame(processed_rows, columns=original_columns)
    
    # Clean the data (keep \n in job titles column)
    for col in df.columns:
        if col != "Examples of related job titles (non-exclusive)":
            df[col] = df[col].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
    
    # Split salary columns (columns 3-6) into amount and rate
    expanded_data = []
    for _, row in df.iterrows():
        new_row = []
        
        # Keep first two columns as is
        new_row.extend([row.iloc[0], row.iloc[1]])
        
        # Split columns 3-6 (salary columns)
        for col_idx in range(2, 6):
            amount, rate = split_salary_data(row.iloc[col_idx])
            new_row.extend([amount, rate])
        
        # Keep last column as is
        new_row.append(row.iloc[6])
        
        expanded_data.append(new_row)
    
    # Define new column names (11 columns total)
    new_columns = [
        "SOC 2020 occupation code",
        "Examples of related job titles (non-exclusive)",
        "Going rate (SW – options A and D) - Amount",
        "Going rate (SW – options A and D) - Rate",
        "90% of going rate (SW – option B) - Amount", 
        "90% of going rate (SW – option B) - Rate",
        "80% of going rate (SW – option C) - Amount",
        "80% of going rate (SW – option C) - Rate", 
        "70% of going rate (SW – option E) - Amount",
        "70% of going rate (SW – option E) - Rate",
        "Eligible for PhD points (SW)?",
    ]
    
    # Create final DataFrame
    final_df = pd.DataFrame(expanded_data, columns=new_columns)
    
    # Remove any completely empty rows
    final_df = final_df.dropna(how='all')
    
    # Filter to ensure we have valid SOC codes
    final_df = final_df[final_df['SOC 2020 occupation code'].astype(str).str.match(r'^\d{4}')]
    
    print(f"Final {table_name} dataset: {len(final_df)} rows x {len(final_df.columns)} columns")
    
    return final_df

def extract_table1_and_table1a(pdf_path, output_filename):
    """Extract both Table 1 and Table 1a data and save to Excel"""
    
    # Extract Table 1 (pages 13-40, but stop at 3556)
    table1_df = extract_table_data(
        pdf_path, 
        start_page=12,  # Page 13 (0-indexed)
        end_page=40,    # Page 40 (0-indexed, exclusive) - extended range
        table_name="Table 1",
        first_row_pattern=r"1111.*Chief executives",
        last_row_pattern=r"3556.*Sales"  # Simplified pattern
    )
    
    # Extract Table 1a (pages 29-70, extended to find 9249)
    table1a_df = extract_table_data(
        pdf_path,
        start_page=28,  # Page 29 (0-indexed) 
        end_page=70,    # Page 70 (0-indexed, exclusive) - extended range
        table_name="Table 1a",
        first_row_pattern=r"1150.*Managers.*retail.*wholesale",  # Should start with this
        last_row_pattern=r"9249.*Elementary.*sales"
    )
    
    # Manual adjustment for Table 1a if it doesn't start correctly
    if table1a_df.empty or not table1a_df['SOC 2020 occupation code'].iloc[0].startswith('1150'):
        print("Table 1a didn't start with 1150, trying alternative extraction...")
        # Try starting from after 3556 in the full extraction with extended range
        all_data_df = extract_table_data(
            pdf_path,
            start_page=12,  # Start from beginning
            end_page=70,    # Go to end (extended range)
            table_name="Full data",
            first_row_pattern=r"1111.*Chief executives", 
            last_row_pattern=r"9249.*Elementary.*sales"
        )
        
        if not all_data_df.empty:
            # Find where 3556 ends and split
            mask_3556 = all_data_df['SOC 2020 occupation code'].str.contains('3556', na=False)
            if mask_3556.any():
                idx_3556 = all_data_df[mask_3556].index[0]
                table1_df = all_data_df.iloc[:idx_3556+1].copy()  # Include 3556
                
                # Find 1150 start for Table 1a
                remaining_data = all_data_df.iloc[idx_3556+1:].copy()
                mask_1150 = remaining_data['SOC 2020 occupation code'].str.contains('1150', na=False)
                if mask_1150.any():
                    idx_1150 = remaining_data[mask_1150].index[0] - (idx_3556+1)
                    table1a_df = remaining_data.iloc[idx_1150:].copy()
                    
                print(f"Manual split: Table 1 ends at 3556 ({len(table1_df)} rows)")
                print(f"Manual split: Table 1a starts at 1150 ({len(table1a_df)} rows)")
    
    # Save to Excel with multiple sheets
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        if not table1_df.empty:
            table1_df.to_excel(writer, sheet_name='Table 1', index=False)
            print(f"Table 1 saved with {len(table1_df)} rows")
        else:
            print("Table 1 is empty - not saved")
            
        if not table1a_df.empty:
            table1a_df.to_excel(writer, sheet_name='Table 1a', index=False)
            print(f"Table 1a saved with {len(table1a_df)} rows")
        else:
            print("Table 1a is empty - not saved")
    
    print(f"Data successfully saved to {output_filename}")
    
    return table1_df, table1a_df

# Main execution
if __name__ == "__main__":
    if not os.path.exists(pdf_path):
        print(f"Error: The file {pdf_path} was not found.")
    else:
        # Extract both tables
        table1_df, table1a_df = extract_table1_and_table1a(pdf_path, "table_1_and_1a_data.xlsx")
        
        # Print summary
        print("\n=== 提取总结 ===")
        print(f"Table 1: {len(table1_df)} 行")
        print(f"Table 1a: {len(table1a_df)} 行")
        print(f"总计: {len(table1_df) + len(table1a_df)} 行")
        
        if not table1_df.empty:
            print(f"Table 1 SOC代码范围: {table1_df.iloc[0, 0]} 到 {table1_df.iloc[-1, 0]}")
        if not table1a_df.empty:
            print(f"Table 1a SOC代码范围: {table1a_df.iloc[0, 0]} 到 {table1a_df.iloc[-1, 0]}") 