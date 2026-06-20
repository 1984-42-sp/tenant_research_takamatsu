from pathlib import Path
import importlib.util
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path,
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

OUTPUT_DIR = ROOT / "output"
LIST_CSV_PATH = OUTPUT_DIR / selectors.OUTPUT_LIST_CSV
DETAIL_CSV_PATH = OUTPUT_DIR / selectors.OUTPUT_DETAIL_CSV
MERGED_CSV_PATH = OUTPUT_DIR / selectors.OUTPUT_MERGED_CSV


def extract_article_id(url):
    match = re.search(r"detail-([^/]+)/?", str(url))

    if match:
        return match.group(1)

    return ""


def main():
    list_df = pd.read_csv(LIST_CSV_PATH)
    detail_df = pd.read_csv(DETAIL_CSV_PATH)

    list_df["article_id"] = list_df["detail_url"].apply(extract_article_id)

    print("==== MERGE ====")
    print(f"list: {list_df.shape}")
    print(f"detail: {detail_df.shape}")

    duplicated_list = list_df["article_id"].duplicated().sum()
    duplicated_detail = detail_df["article_id"].duplicated().sum()

    print(f"duplicated list article_id: {duplicated_list}")
    print(f"duplicated detail article_id: {duplicated_detail}")

    merged_df = pd.merge(
        list_df,
        detail_df,
        on="article_id",
        how="left",
        suffixes=("_list", "_detail"),
    )

    print(f"merged: {merged_df.shape}")
    print(f"expected rows: {selectors.EXPECTED_LIST_COUNT}")

    if len(merged_df) != selectors.EXPECTED_LIST_COUNT:
        print("WARNING: merged rows count does not match expected count")

    missing_detail = merged_df["title"].isna().sum() if "title" in merged_df.columns else len(merged_df)
    print(f"missing detail rows: {missing_detail}")

    merged_df.to_csv(MERGED_CSV_PATH, index=False, encoding="utf-8-sig")

    print(f"saved: {MERGED_CSV_PATH}")


if __name__ == "__main__":
    main()