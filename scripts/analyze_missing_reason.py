from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"

df = pd.read_csv(CSV_PATH)

check_df = df[df["事業成立パターン"] == "要確認・情報不足型"].copy()

def is_missing(value):
    if pd.isna(value):
        return True
    return str(value).strip() == ""

def missing_reason(row):
    rent_missing = is_missing(row.get("家賃_円"))
    tsubo_missing = is_missing(row.get("坪数_補正"))

    if rent_missing and tsubo_missing:
        return "家賃・面積不明"
    if rent_missing:
        return "家賃未定"
    if tsubo_missing:
        return "面積不明"
    return "算定条件不足"

check_df["不足理由"] = check_df.apply(missing_reason, axis=1)

print("=== 要確認件数 ===")
print(len(check_df))

print("\n=== 不足理由 ===")
print(check_df["不足理由"].value_counts())

print("\n=== サイト別 不足理由 ===")
print(pd.crosstab(check_df["掲載サイト"], check_df["不足理由"]))

print("\n=== 要確認一覧 ===")
cols = [
    "物件名",
    "掲載サイト",
    "家賃",
    "面積",
    "坪数",
    "家賃_円",
    "坪数_補正",
    "不足理由",
]
print(check_df[cols].to_string(index=False))