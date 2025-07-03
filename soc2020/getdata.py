#!/usr/bin/env python3
"""
build_soc2020_prisma.py
 - Rebuilds schema.prisma & seed.ts with Skilled-Worker flag handled correctly.
"""
import json, pathlib, textwrap, re, pandas as pd

SOC_FILE      = "soc2020volume1structureanddescriptionofunitgroupsexcel16042025.xlsx"
ELIGIBLE_FILE = "eligible_occupations.xlsx"

# ──────────────────────────────────────────────────────────────────────────────
# 1. Load SOC2020 sheets
# ──────────────────────────────────────────────────────────────────────────────
desc = pd.read_excel(SOC_FILE, sheet_name="SOC2020 descriptions", dtype=str).replace({"<blank>": None})
fw   = pd.read_excel(SOC_FILE, sheet_name="SOC2020 Framework",   dtype=str).replace({"<blank>": None})

fw_units = fw[fw["SOC2020 Unit Group"].notna()]
fw_major = fw[(fw["SOC2020\nMajor Group"].notna()) & fw["SOC2020 Unit Group"].isna()]
fw_sub   = fw[(fw["SOC2020\nSub-Major Group"].notna()) & fw["SOC2020 Unit Group"].isna()]
fw_minor = fw[(fw["SOC2020\nMinor Group"].notna()) & fw["SOC2020 Unit Group"].isna()]

units = desc[desc["SOC 2020 Unit Group"].notna()]

# ──────────────────────────────────────────────────────────────────────────────
# 2. Maps: code ➜ title
# ──────────────────────────────────────────────────────────────────────────────
major_title = {int(c): t for c, t in zip(fw_major["SOC2020\nMajor Group"],  fw_major["SOC2020 Group Title"])}
sub_title   = {int(c): t for c, t in zip(fw_sub["SOC2020\nSub-Major Group"], fw_sub["SOC2020 Group Title"])}
minor_title = {int(c): t for c, t in zip(fw_minor["SOC2020\nMinor Group"],   fw_minor["SOC2020 Group Title"])}

# ──────────────────────────────────────────────────────────────────────────────
# 3. Build eligibility map  (code -> True/False)
# ──────────────────────────────────────────────────────────────────────────────
elig_df = pd.read_excel(ELIGIBLE_FILE, sheet_name=0, dtype=str)

code_col = next(c for c in elig_df.columns if re.search(r"code", c, re.I))
elig_col = next(c for c in elig_df.columns if re.search(r"eligible", c, re.I))

elig_df["elig_bool"] = elig_df[elig_col].str.strip().str.lower().isin(["yes", "y", "true", "1"])

# same code may appear multiple times; use `.max()` so any Yes wins
eligibility_map = {
    int(code): bool(flag)
    for code, flag in (
        elig_df
        .dropna(subset=[code_col])
        .assign(code_int=lambda d: d[code_col].str.strip())
        .query("code_int.str.isdigit()")
        .groupby("code_int")["elig_bool"]
        .max()
        .items()
    )
}

# ──────────────────────────────────────────────────────────────────────────────
# 4. Merge for Unique-ID & assemble records
# ──────────────────────────────────────────────────────────────────────────────
joined = units.merge(
    fw_units[["Unique ID", "SOC2020 Unit Group"]],
    left_on="SOC 2020 Unit Group",
    right_on="SOC2020 Unit Group",
    how="left",
    validate="1:1",
)

assert joined["Unique ID"].notna().all(), "Some Unit-Groups are missing Unique ID"

def clean_list(x):
    return [t.lstrip("~").strip() for t in str(x).splitlines() if t.strip()] if x else []

records = []
for _, r in joined.iterrows():
    ug = int(r["SOC 2020 Unit Group"])   # 4-digit code
    major, sub, minor = ug // 1000, ug // 100, ug // 10

    records.append(
        {
            "id": r["Unique ID"],

            "majorGroup": major,
            "majorGroupTitle":  major_title[major],
            "subMajorGroup":    sub,
            "subMajorGroupTitle": sub_title[sub],
            "minorGroup":       minor,
            "minorGroupTitle":  minor_title[minor],

            "unitGroup": ug,
            "groupTitle": r["SOC\n2020 \nGroup Title"].strip(),

            "groupsClassifiedWithin": r["Groups Classified Within Sub-Groups "] or None,
            "groupDescription":       r["Group  Description"] or None,
            "entryRoutes":            r["Typical Entry Routes And Associated Qualifications"] or None,
            "tasks":                  r["Tasks"] or None,
            "relatedJobTitles":       clean_list(r["Related Job Titles"]),

            "eligibleForSkilledWorker": eligibility_map.get(ug, False),
        }
    )

# ──────────────────────────────────────────────────────────────────────────────
# 5. Prisma schema
# ──────────────────────────────────────────────────────────────────────────────
schema = textwrap.dedent("""
    datasource db {
      provider = "postgresql"
      url      = env("DATABASE_URL")
    }

    generator client {
      provider = "prisma-client-js"
    }

    model Soc2020 {
      id                     String  @id

      majorGroup             Int
      majorGroupTitle        String
      subMajorGroup          Int
      subMajorGroupTitle     String
      minorGroup             Int
      minorGroupTitle        String

      unitGroup              Int
      groupTitle             String

      groupsClassifiedWithin String?
      groupDescription       String?
      entryRoutes            String?
      tasks                  String?
      relatedJobTitles       String[]

      eligibleForSkilledWorker Boolean @default(false)
    }
""").lstrip()

# ──────────────────────────────────────────────────────────────────────────────
# 6. seed.ts
# ──────────────────────────────────────────────────────────────────────────────
seed_ts = textwrap.dedent(f"""
    import {{ PrismaClient }} from '@prisma/client';
    const prisma = new PrismaClient();

    const data = {json.dumps(records, ensure_ascii=False, indent=2)};

    async function main() {{
      await prisma.soc2020.createMany({{ data }});
    }}

    main()
      .catch(e => {{ console.error(e); process.exit(1); }})
      .finally(() => prisma.$disconnect());
""").lstrip()

# ──────────────────────────────────────────────────────────────────────────────
# 7. Write files
# ──────────────────────────────────────────────────────────────────────────────
pathlib.Path("schema.prisma").write_text(schema, encoding="utf-8")
pathlib.Path("seed.ts").write_text(seed_ts, encoding="utf-8")

print(f"✅  Rebuilt schema.prisma & seed.ts – {len(records)} rows; Skilled-Worker flag is correct.")
