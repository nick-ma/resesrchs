#!/usr/bin/env python3
"""
illegal_penalties_workflow.py
––––––––––––––––––––––––––––––
• Scrapes the GOV-UK list of illegal-working civil penalties
  for 1 July – 30 September 2024.
• Parses the table into a DataFrame.
• Enriches each row with:
    – Companies-House company number
    – SIC (industry) codes
    – All director nationalities
• Writes the enriched data to Excel (sheet 1).
• Generates a back-of-the-envelope forecast for 2025 Q1 & Q2
  using simple growth factors; saves that in sheet 2.

Dependencies
------------
    pip install requests beautifulsoup4 pandas openpyxl tqdm

Environment
-----------
    export CH_KEY="YOUR_COMPANIES_HOUSE_API_KEY"
"""

import os, re, time, requests, pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from tqdm import tqdm


GOV_URL = (
    "https://www.gov.uk/government/publications/"
    "illegal-working-penalties-uk-report/"
    "illegal-working-civil-penalties-for-uk-employers-1-july-to-30-september-2024"
)
CH_KEY = os.getenv("CH_KEY")  # Companies House API key (free –  calls are rate-limited)


# ------------------------------------------------------------------
# 1. Scrape GOV-UK table
# ------------------------------------------------------------------
def fetch_rows(url: str = GOV_URL) -> list[list[str]]:
    """Return every row from the HTML table."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        raise RuntimeError("No table found – GOV.UK changed the page layout?")
    
    rows = []
    # Find all `tr` elements in the `tbody`
    for tr in table.find("tbody").find_all("tr"):
        # For each `tr`, find all `td` elements and get their text
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if cells:
            rows.append(cells)

    if not rows:
        raise RuntimeError("No rows found – GOV.UK changed the page layout?")
    return rows


# ------------------------------------------------------------------
# 2. Parse each row
# ------------------------------------------------------------------



def parse(row: list[str]) -> dict | None:
    """Extracts data from a single table row."""
    if len(row) != 5:
        return None  # Skip rows that don't have exactly 5 columns

    liable_party, business_name, address, postcode, penalty_str = row

    try:
        # Clean the penalty value, removing currency symbols, commas, and zero-width spaces
        penalty_val = float(
            penalty_str.replace("£", "").replace(",", "").replace("\u200b", "").strip()
        )
    except (ValueError, IndexError):
        return None

    return {
        "liable_party": liable_party.strip(),
        "business_name": business_name.strip(),
        "address": address.strip(),
        "postcode": postcode.strip(),
        "penalty_value": penalty_val,
    }


# ------------------------------------------------------------------
# 3. Companies House helpers
# ------------------------------------------------------------------
def ch_get(endpoint: str):
    if not CH_KEY:
        return None
    url = f"https://api.company-information.service.gov.uk{endpoint}"
    r = requests.get(url, auth=(CH_KEY, ""), timeout=20)
    return r.json() if r.status_code == 200 else None


def ch_match_company(name: str) -> tuple[str | None, str]:
    """Return (company_number, official_title) or (None, "")."""
    res = ch_get(f"/search/companies?q={quote_plus(name)}&items_per_page=1")
    if not res or not res.get("items"):
        return None, ""
    item = res["items"][0]
    return item["company_number"], item.get("title", "")


def ch_company_details(num: str) -> dict:
    data = ch_get(f"/company/{num}") or {}
    officers = ch_get(f"/company/{num}/officers?items_per_page=100") or {}
    nats = {
        o.get("nationality", "").title()
        for o in officers.get("items", [])
        if o.get("nationality")
    }
    return {
        "sic_codes": ";".join(data.get("sic_codes", [])),
        "director_nationalities": ";".join(sorted(nats)),
        "status": data.get("company_status", ""),
    }


# ------------------------------------------------------------------
# 4. Forecast (very crude)
# ------------------------------------------------------------------
def forecast(df: pd.DataFrame, q1_growth=0.15, q2_growth=0.25) -> pd.DataFrame:
    base = df["penalty_value"].sum()
    regional_share = df.groupby("postcode")["penalty_value"].sum() / base
    records = []
    for label, g in [("2025_Q1", q1_growth), ("2025_Q2", q2_growth)]:
        total = base * (1 + g)
        for pc, share in regional_share.items():
            records.append(
                {
                    "period": label,
                    "postcode": pc or "n/a",
                    "forecast_penalty": round(total * share, 2),
                }
            )
    return pd.DataFrame.from_records(records)


# ------------------------------------------------------------------
# 5. Main orchestration
# ------------------------------------------------------------------
def main():
    print("Downloading GOV-UK page …")
    raw_rows = fetch_rows()
    parsed = [p for r in raw_rows if (p := parse(r))]
    df = pd.DataFrame(parsed)
    print(f"Parsed {len(df):,} rows")

    if df.empty:
        print("No data parsed from GOV-UK page, cannot proceed.")
        return

    # — Companies House enrichment —
    if CH_KEY:
        extra = []
        for nm in tqdm(df["liable_party"], desc="Companies House"):
            num, official = ch_match_company(nm)
            dets = ch_company_details(num) if num else {}
            extra.append(
                {
                    "company_number": num or "",
                    "official_title": official,
                    **dets,
                }
            )
            time.sleep(0.2)  # stay polite to the API
        df = pd.concat([df.reset_index(drop=True), pd.DataFrame(extra)], axis=1)
    else:
        print("CH_KEY not set – skipping Companies House enrichment")

    # — Forecast —
    fc = forecast(df)

    # — Write Excel —
    out_file = "illegal_working_Q3_2024_enriched.xlsx"
    with pd.ExcelWriter(out_file, engine="openpyxl") as xls:
        df.to_excel(xls, sheet_name="2024_Q3_enriched", index=False)
        fc.to_excel(xls, sheet_name="forecast_2025_Q1_Q2", index=False)

    print(f"Excel written → {out_file}")


if __name__ == "__main__":
    main()
