import pdfplumber
import pandas as pd
import os
import re

# Define the correct absolute path for the PDF file
pdf_path = os.path.abspath("E03394848_-_HC_997_-_Immigration_Rules_Changes__Web_Accessible_.pdf")

def extract_table_data(pdf_path, table_name, start_marker, end_marker, output_filename):
    all_rows = []
    start_page = -1

    with pdfplumber.open(pdf_path) as pdf:
        end_page_actual = len(pdf.pages)
        # Find start and end pages for the specified table
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                if start_marker in text:
                    if start_page == -1:
                        start_page = i
                if end_marker and end_marker in text:
                    end_page_actual = i + 1  # Process up to and including this page
                    break
        
        if start_page != -1:
            # Extract tables from the identified pages
            for i in range(start_page, end_page_actual):
                page = pdf.pages[i]
                tables = page.extract_tables()
                for table in tables:
                    all_rows.extend(table)

    if all_rows:
        # Debugging: Print raw all_rows for Table 1 and Table 2
        if table_name == "Table 1" or table_name == "Table 2":
            print(f"\n--- Raw all_rows for {table_name} ---")
            for idx, row in enumerate(all_rows):
                print(f"Row {idx} length: {len(row)}")
                print(row)

        # Manually define the header because it is complex in the PDF
        # Use a different header for Table 2 if its structure is different
        if table_name == "Table 2":
            header = [
                "SOC 2020 occupation code",
                "Equivalent SOC 2010 occupation code(s)",
                "Examples of related job titles (non-exclusive)",
                "Going rate (SW – options F and I, GBM and SCU)",
                "90% of going rate (SW – option G)",
                "80% of going rate (SW – option H)",
                "70% of going rate (SW – option J, GTR)",
                "Eligible for PhD points (SW)?",
            ]
        else:
            header = [
                "SOC 2020 occupation code",
                "Examples of related job titles (non-exclusive)",
                "Going rate (SW – options A and D)",
                "90% of going rate (SW – option B)",
                "80% of going rate (SW – option C)",
                "70% of going rate (SW – option E)",
                "Eligible for PhD points (SW)?",
            ]

        # Find the start of the actual data by looking for the first row that looks like data
        data_start_index = 0
        for i, row in enumerate(all_rows):
            if row and row[0] and str(row[0]).strip().isdigit():
                data_start_index = i
                break

        if table_name == "Table 1" or table_name == "Table 2":
            print(f"data_start_index for {table_name}: {data_start_index}")
            print(f"\n--- all_rows[data_start_index:] for {table_name} ---")
            for idx, row in enumerate(all_rows[data_start_index:]):
                print(f"Row {idx} (after slice) length: {len(row)}")
                print(row)

        # Create a DataFrame with the correct header and data
        df = pd.DataFrame(all_rows[data_start_index:], columns=header)

        # Clean the data
        df = df.applymap(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
        df = df.dropna(how='all')

        # Filter rows to keep only those where 'SOC 2020 occupation code' starts with a 4-digit number
        df = df[df['SOC 2020 occupation code'].astype(str).str.match(r"^\s*\d{4}")]

        output_excel_path = output_filename
        df.to_excel(output_excel_path, index=False)

        print(f"{table_name} data has been successfully extracted and saved to {output_excel_path}")
    else:
        print(f"Could not find or extract {table_name} from the PDF.")


# Main execution
if not os.path.exists(pdf_path):
    print(f"Error: The file {pdf_path} was not found.")
else:
    # Extract Table 1
    extract_table_data(
        pdf_path,
        "Table 1",
        "Table 1: Eligible SOC 2020 occupation codes",
        "Table 2: Eligible SOC 2020 occupation codes for Health and Care Worker visa",
        "table_1_data.xlsx"
    )

    # Extract Table 2
    extract_table_data(
        pdf_path,
        "Table 2",
        "Table 2: Eligible SOC 2020 occupation codes for Health and Care Worker visa",
        None, # No explicit end marker found, extract until end of document
        "table_2_data.xlsx"
    )
