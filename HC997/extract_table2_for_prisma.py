import pandas as pd
import json
from pathlib import Path

def clean_money(value):
    """清洗货币值，去除 £ 和逗号，保留两位小数"""
    if isinstance(value, str):
        value = value.replace("£", "").replace(",", "").strip()
    try:
        return round(float(value), 2)
    except:
        return None

def main():
    # 文件路径和工作表名
    excel_path = Path("table_2_and_related_data.xlsx")
    sheet_name = "Table 2"

    if not excel_path.exists():
        raise FileNotFoundError(f"❌ 文件不存在: {excel_path.resolve()}")

    # 读取 Excel
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

    # 清理空行空列
    df = df.dropna(how="all").dropna(axis=1, how="all")

    # 清洗第一列：SOC code + title
    first_col = df.columns[0]
    df[first_col] = df[first_col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    df[['unitGroup', 'groupTitle']] = df[first_col].str.extract(r'^([0-9]{4})\s+(.*)$')
    df = df.drop(columns=[first_col])
    df = df.dropna(subset=["unitGroup", "groupTitle"])
    df["unitGroup"] = df["unitGroup"].astype(int)

    # 字段映射：schema → Excel列名
    column_map = {
        "equivalentUnitGroups": "Equivalent SOC 2010 occupation code(s)",
        "rateFIAmount": "Going rate amount (SW – options F and I, GBM and SCU)",
        "rateFIRate": "Going rate per hour (SW – options F and I, GBM and SCU)",
        "rateGAmount": "90% going rate amount (SW – option G)",
        "rateGRate": "90% going rate per hour (SW – option G)",
        "rateHAmount": "80% going rate amount (SW – option H)",
        "rateHRate": "80% going rate per hour (SW – option H)",
        "rateJAmount": "70% going rate amount (SW – option J, GTR)",
        "rateJRate": "70% going rate per hour (SW – option J, GTR)",
        "eligibleForPhD": "Eligible for PhD points (SW)?"
    }

    # 统一处理空值
    df = df.replace(["Not applicable", "N/A", "n/a", "NA", ""], None)
    df = df.where(pd.notnull(df), None)

    # 执行字段映射并清洗值
    for field, source_col in column_map.items():
        if source_col not in df.columns:
            df[field] = None
        elif "amount" in field.lower() or "rate" in field.lower():
            df[field] = df[source_col].apply(clean_money)
        elif "eligibleForPhD" == field:
            df[field] = df[source_col].apply(
                lambda x: str(x).strip().lower() == "yes" if x is not None else None
            )
        else:
            df[field] = df[source_col]
        if source_col in df.columns:
            df = df.drop(columns=[source_col])

    # 按目标字段顺序输出
    final_columns = [
        "unitGroup", "groupTitle", "equivalentUnitGroups",
        "rateFIAmount", "rateFIRate", "rateGAmount", "rateGRate",
        "rateHAmount", "rateHRate", "rateJAmount", "rateJRate",
        "eligibleForPhD"
    ]
    df = df[final_columns]

    # 输出 JSON
    records = df.to_dict(orient="records")
    output_path = Path("table2_mapped_to_schema.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✅ 已成功写入：{output_path.resolve()}")
    print(f"📊 共导出 {len(records)} 条记录，字段数：{len(df.columns)}")

if __name__ == "__main__":
    main()
