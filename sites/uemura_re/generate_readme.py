from pathlib import Path

import pandas as pd
import selectors

SITE_DIR = Path("sites") / "uemura_re"
OUT_DIR = Path("output") / "uemura_re"

LIST_CSV = OUT_DIR / "uemura_re_list.csv"
DETAIL_CSV = OUT_DIR / "uemura_re_detail.csv"
MERGED_CSV = OUT_DIR / "uemura_re.csv"
GEOCODED_CSV = OUT_DIR / "uemura_re_geocoded.csv"
FAILED_CSV = OUT_DIR / "uemura_re_geocode_failed.csv"

MAP_HTML = Path("output") / "uemura_re_map.html"
README_PATH = SITE_DIR / "README.md"


def shape_text(path: Path) -> str:
    if not path.exists():
        return "未生成"

    df = pd.read_csv(path)
    return f"{len(df)}件 / {len(df.columns)}列"


def exists_text(path: Path) -> str:
    return "生成済み" if path.exists() else "未生成"


def main():
    readme_lines = [
        f"# {selectors.SITE_LABEL}",
        "",
        "## サイト情報",
        "",
        f"- サイト名: {selectors.SITE_LABEL}",
        f"- ベースURL: {selectors.BASE_URL}",
        f"- 一覧URL: {selectors.LIST_URLS[0]['url']}",
        f"- 追加詳細URL: {selectors.EXTRA_DETAIL_URLS[0]['url']}",
        "",
        "## 取得結果",
        "",
        f"- 一覧CSV: {shape_text(LIST_CSV)}",
        f"- 詳細CSV: {shape_text(DETAIL_CSV)}",
        f"- 統合CSV: {shape_text(MERGED_CSV)}",
        f"- ジオコード済みCSV: {shape_text(GEOCODED_CSV)}",
        f"- ジオコード失敗CSV: {shape_text(FAILED_CSV)}",
        f"- 地図HTML: {exists_text(MAP_HTML)}",
        "",
        "## 件数",
        "",
        f"- 貸店舗一覧: {selectors.EXPECTED_LIST_COUNT}件",
        f"- 貸ビル・貸倉庫・その他: {selectors.EXPECTED_EXTRA_DETAIL_COUNT}件",
        f"- 合計: {selectors.EXPECTED_TOTAL_COUNT}件",
        "",
        "## 実行順序",
        "",
        "```powershell",
        "python sites\\uemura_re\\fetch_list.py",
        "python sites\\uemura_re\\inspect_list.py",
        "python sites\\uemura_re\\extract.py",
        "python sites\\uemura_re\\fetch_detail.py",
        "python sites\\uemura_re\\inspect_detail.py",
        "python sites\\uemura_re\\extract_detail.py",
        "python sites\\uemura_re\\merge.py",
        "python sites\\uemura_re\\map.py",
        "python sites\\uemura_re\\generate_readme.py",
        "```",
        "",
        "## 成果物",
        "",
        "```text",
        "output/uemura_re/uemura_re_list.csv",
        "output/uemura_re/uemura_re_detail.csv",
        "output/uemura_re/uemura_re.csv",
        "output/uemura_re/uemura_re_geocoded.csv",
        "output/uemura_re/uemura_re_geocode_failed.csv",
        "output/uemura_re_map.html",
        "sites/uemura_re/selectors.py",
        "sites/uemura_re/README.md",
        "```",
        "",
        "## 備考",
        "",
        "- 一覧ページは1ページ。",
        "- 貸店舗4件を一覧から取得。",
        "- 貸ビル・貸倉庫・その他1件は詳細URLを直接追加。",
        "- 詳細ページは5件取得。",
        "- ジオコード成功4件、失敗1件。",
        "",
    ]

    README_PATH.write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"saved: {README_PATH}")


if __name__ == "__main__":
    main()