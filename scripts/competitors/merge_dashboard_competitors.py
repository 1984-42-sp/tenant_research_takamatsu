from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_BUSINESS_PLAN = (
    BASE_DIR
    / "output"
    / "archive_csv"
    / "business_plan_dashboard.csv"
)

INPUT_COMPETITOR_SUMMARY = (
    BASE_DIR
    / "output"
    / "competitors"
    / "property_competitor_summary.csv"
)

OUT_PATH = (
    BASE_DIR
    / "output"
    / "competitors"
    / "business_plan_dashboard_with_competitors.csv"
)


ADD_COLUMNS = [
    "nearby_500m_count",
    "nearby_1000m_count",
    "nearest_competitor_name",
    "nearest_competitor_distance_m",
]


def main():
    if not INPUT_BUSINESS_PLAN.exists():
        raise FileNotFoundError(f"入力CSVがありません: {INPUT_BUSINESS_PLAN}")

    if not INPUT_COMPETITOR_SUMMARY.exists():
        raise FileNotFoundError(f"競合サマリーCSVがありません: {INPUT_COMPETITOR_SUMMARY}")

    df = pd.read_csv(INPUT_BUSINESS_PLAN, dtype=str).fillna("")
    summary = pd.read_csv(INPUT_COMPETITOR_SUMMARY, dtype=str).fillna("")

    for col in ADD_COLUMNS:
        if col not in summary.columns:
            summary[col] = ""

    summary = summary[
        [
            "物件名",
            "nearby_500m_count",
            "nearby_1000m_count",
            "nearest_competitor_name",
            "nearest_competitor_distance_m",
        ]
    ].copy()

    merged = df.merge(
        summary,
        on="物件名",
        how="left",
    )

    for col in ADD_COLUMNS:
        merged[col] = merged[col].fillna("")
        merged[col] = merged[col].replace("", "0") if "count" in col else merged[col]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[LOAD] business_plan: {INPUT_BUSINESS_PLAN} / {len(df)} rows")
    print(f"[LOAD] summary: {INPUT_COMPETITOR_SUMMARY} / {len(summary)} rows")
    print(f"[SAVE] {OUT_PATH} / {len(merged)} rows")


if __name__ == "__main__":
    main()