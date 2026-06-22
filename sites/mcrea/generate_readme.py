from pathlib import Path

import pandas as pd
import selectors

SITE_DIR = Path("sites") / "mcrea"
OUT_DIR = Path("output") / "mcrea"

LIST_CSV = OUT_DIR / "mcrea_list.csv"
DETAIL_CSV = OUT_DIR / "mcrea_detail.csv"
MERGED_CSV = OUT_DIR / "mcrea.csv"
GEOCODED_CSV = OUT_DIR / "mcrea_geocoded.csv"
FAILED_CSV = OUT_DIR / "mcrea_geocode_failed.csv"

MAP_HTML = OUT_DIR / "mcrea_map.html"
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
        f"- 一覧URL1: {selectors.LIST_URLS[0]['url']}",
        f"- 一覧URL2: {selectors.LIST_URLS[1]['url']}",
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
        f"- 一覧取得: {selectors.EXPECTED_LIST_COUNT}件",
        f"- 詳細取得: {selectors.EXPECTED_TOTAL_COUNT}件",
        f"- ジオコード成功: 41件",
        f"- ジオコード失敗: 1件",
        "",
        "## 実行順序",
        "",
        "```powershell",
        "python sites\\mcrea\\fetch_list_manual.py",
        "python sites\\mcrea\\inspect_list.py",
        "python sites\\mcrea\\extract.py",
        "python sites\\mcrea\\fetch_detail.py",
        "python sites\\mcrea\\inspect_detail.py",
        "python sites\\mcrea\\extract_detail.py",
        "python sites\\mcrea\\merge.py",
        "python sites\\mcrea\\map.py",
        "python sites\\mcrea\\generate_readme.py",
        "```",
        "",
        "## 成果物",
        "",
        "```text",
        "output/mcrea/mcrea_list.csv",
        "output/mcrea/mcrea_detail.csv",
        "output/mcrea/mcrea.csv",
        "output/mcrea/mcrea_geocoded.csv",
        "output/mcrea/mcrea_geocode_failed.csv",
        "output/mcrea_map.html",
        "sites/mcrea/selectors.py",
        "sites/mcrea/README.md",
        "```",
        "",
        "## 備考",
        "",
        "- 一覧は2ページ。",
        "- 高松市＋飲食店可の条件で42件を取得。",
        "- 通常のrequests直取得では飲食店可条件が外れるため、fetch_list_manual.pyで手動検索後にHTML保存した。",
        "- mcrea.jpは接続が不安定で、Playwright timeout / ReadTimeout / SSL handshake timeout が発生した。",
        "- 詳細HTML取得では retry / skip / sleep / Connection: close を使用した。",
        "- 今後のテンプレートには fetch_with_retry、既取得ファイルskip、sleep制御を標準搭載することを推奨。",
        "",
    ]

    README_PATH.write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"saved: {README_PATH}")


if __name__ == "__main__":
    main()