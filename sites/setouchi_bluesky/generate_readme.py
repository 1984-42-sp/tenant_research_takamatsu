from pathlib import Path
import importlib.util

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

OUTPUT_SITE_DIR = ROOT / "output" / selectors.SITE_NAME

CSV_PATH = OUTPUT_SITE_DIR / selectors.OUTPUT_MERGED_CSV
DETAIL_CSV_PATH = OUTPUT_SITE_DIR / selectors.OUTPUT_DETAIL_CSV
GEOCODED_CSV_PATH = OUTPUT_SITE_DIR / selectors.OUTPUT_GEOCODED_CSV
GEOCODE_FAILED_CSV_PATH = OUTPUT_SITE_DIR / selectors.OUTPUT_GEOCODE_FAILED_CSV
MAP_PATH = ROOT / "output" / selectors.OUTPUT_MAP_HTML

README_PATH = SITE_DIR / "README.md"


def count_csv(path):
    if not path.exists():
        return 0
    return len(pd.read_csv(path))


def main():
    total_count = count_csv(CSV_PATH)
    detail_count = count_csv(DETAIL_CSV_PATH)
    geocoded_count = count_csv(GEOCODED_CSV_PATH)
    geocode_failed_count = count_csv(GEOCODE_FAILED_CSV_PATH)

    df = pd.read_csv(CSV_PATH)

    food_counts = {}
    if "飲食店可否" in df.columns:
        food_counts = df["飲食店可否"].fillna("不明").value_counts().to_dict()

    lines = [
        f"# {selectors.SITE_LABEL}",
        "",
        "## サイト情報",
        "",
        f"- サイト名: {selectors.SITE_LABEL}",
        f"- トップURL: {selectors.BASE_URL}",
        f"- 一覧URL: {selectors.LIST_URL}",
        "- 対象エリア: 高松市",
        "- 対象種別: 貸店舗・テナント",
        "",
        "## 取得結果",
        "",
        f"- 一覧取得件数: {selectors.EXPECTED_LIST_COUNT}",
        f"- 詳細取得件数: {detail_count}",
        f"- 統合CSV件数: {total_count}",
        f"- ジオコーディング成功件数: {geocoded_count}",
        f"- ジオコーディング失敗件数: {geocode_failed_count}",
        "",
        "## 飲食店可否",
        "",
        f"- 可: {food_counts.get('可', 0)}",
        f"- 不可: {food_counts.get('不可', 0)}",
        f"- 不明: {food_counts.get('不明', 0)}",
        "",
        "## 成果物",
        "",
        f"### output/{selectors.SITE_NAME}/",
        "",
        f"- {selectors.OUTPUT_LIST_CSV}",
        f"- {selectors.OUTPUT_DETAIL_CSV}",
        f"- {selectors.OUTPUT_MERGED_CSV}",
        f"- {selectors.OUTPUT_GEOCODED_CSV}",
        f"- {selectors.OUTPUT_GEOCODE_FAILED_CSV}",
        "",
        "### output/",
        "",
        f"- {selectors.OUTPUT_MAP_HTML}",
        "",
        "## 実行順序",
        "",
        "```powershell",
        f"python sites\\{selectors.SITE_NAME}\\fetch_list.py",
        f"python sites\\{selectors.SITE_NAME}\\inspect_list.py",
        f"python sites\\{selectors.SITE_NAME}\\extract.py",
        f"python sites\\{selectors.SITE_NAME}\\fetch_detail.py",
        f"python sites\\{selectors.SITE_NAME}\\inspect_detail.py",
        f"python sites\\{selectors.SITE_NAME}\\extract_detail.py",
        f"python sites\\{selectors.SITE_NAME}\\merge.py",
        f"python sites\\{selectors.SITE_NAME}\\map.py",
        f"python sites\\{selectors.SITE_NAME}\\generate_readme.py",
        "```",
        "",
        "## 備考",
        "",
        "- 一覧ページは1ページ構成。",
        "- 一覧表示件数は5件。",
        "- 詳細HTMLは5件取得済み。",
        "- 詳細情報は table / th / td 構造から抽出。",
        "- 飲食店可否は「特記事項」「title」「設備」「備考」から判定。",
        "",
    ]

    README_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved: {README_PATH}")


if __name__ == "__main__":
    main()