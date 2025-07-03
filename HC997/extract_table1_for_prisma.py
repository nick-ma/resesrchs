import pandas as pd
import json
from pathlib import Path

def clean_money(value):
    """清洗货币值：去除 £ 和逗号，转换为保留两位小数的 float"""
    if isinstance(value, str):
        value = value.replace("£", "").replace(",", "").strip()
    try:
        return round(float(value), 2)
    except:
        return None

def main():
    # 设置文件路径和工作表名
    excel_path = Path("table_1_and_1a_data.xlsx")
    sheet_name = "Table 1"

    if not excel_path.exists():
        raise FileNotFoundError(f"❌ 文件不存在: {excel_path.resolve()}")

    # 读取 Excel
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

    # 删除空行和空列
    df = df.dropna(how="all").dropna(axis=1, how="all")

    # 提取第一列为 unitGroup 和 groupTitle
    first_col = df.columns[0]
    df[first_col] = df[first_col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    df[['unitGroup', 'groupTitle']] = df[first_col].str.extract(r'^([0-9]{4})\s+(.*)$')
    df = df.drop(columns=[first_col])
    df = df.dropna(subset=["unitGroup", "groupTitle"])
    df["unitGroup"] = df["unitGroup"].astype(int)

    # 映射列名（schema 字段 → Excel 中的列名）
    column_map = {
        "rateADAmount": "Going rate (SW – options A and D) - Amount",
        "rateADRate": "Going rate (SW – options A and D) - Rate",
        "rateBAmount": "90% of going rate (SW – option B) - Amount",
        "rateBRate": "90% of going rate (SW – option B) - Rate",
        "rateCAmount": "80% of going rate (SW – option C) - Amount",
        "rateCRate": "80% of going rate (SW – option C) - Rate",
        "rateEAmount": "70% of going rate (SW – option E) - Amount",
        "rateERate": "70% of going rate (SW – option E) - Rate",
        "eligibleForPhD": "Eligible for PhD points (SW)?"
    }

    # 替换空值
    df = df.replace(["Not applicable", "N/A", "n/a", "NA", ""], None)
    df = df.where(pd.notnull(df), None)

    # 执行字段映射并清洗数据
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

    # 按照 schema 字段顺序组织
    final_columns = [
        "unitGroup", "groupTitle",
        "rateADAmount", "rateADRate",
        "rateBAmount", "rateBRate",
        "rateCAmount", "rateCRate",
        "rateEAmount", "rateERate",
        "eligibleForPhD"
    ]
    df = df[final_columns]

    # 导出为 JSON 文件
    records = df.to_dict(orient="records")
    output_path = Path("table1_mapped_to_schema.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✅ 已成功写入：{output_path.resolve()}")
    print(f"📊 共导出 {len(records)} 条记录，字段数：{len(df.columns)}")

if __name__ == "__main__":
    main()
