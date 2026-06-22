from pathlib import Path

import pandas as pd
import selectors

SITE_DIR = Path("sites") / "tenant_shop"
OUT_DIR = Path("output") / "tenant_shop"

DETAIL_CSV = OUT_DIR / "tenant_shop_detail.csv"
MERGED_CSV = OUT_DIR / "tenant_shop.csv"
GEOCODED_CSV = OUT_DIR / "tenant_shop_geocoded.csv"
FAILED_CSV = OUT_DIR / "tenant_shop_geocode_failed.csv"

MAP_HTML = OUT_DIR / "tenant_shop_map.html"
README_PATH = SITE_DIR / "README.md"


def shape_text(path: Path) -> str:
    if not path.exists():
        return "未生成"

    if path.stat().st_size == 0:
        return "0件 / 0列"

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return "0件 / 0列"

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
        f"- 詳細URL: {selectors.DETAIL_URLS[0]}",
        "",
        "## 取得結果",
        "",
        f"- 詳細CSV: {shape_text(DETAIL_CSV)}",
        f"- 統合CSV: {shape_text(MERGED_CSV)}",
        f"- ジオコード済みCSV: {shape_text(GEOCODED_CSV)}",
        f"- ジオコード失敗CSV: {shape_text(FAILED_CSV)}",
        f"- 地図HTML: {exists_text(MAP_HTML)}",
        "",
        "## 件数",
        "",
        "- 詳細取得: 1件",
        "- ジオコード成功: 1件",
        "- ジオコード失敗: 0件",
        "",
        "## 実行順序",
        "",
        "```powershell",
        "python sites\\tenant_shop\\fetch_detail.py",
        "python sites\\tenant_shop\\inspect_detail.py",
        "python sites\\tenant_shop\\extract_detail.py",
        "python sites\\tenant_shop\\merge.py",
        "python sites\\tenant_shop\\map.py",
        "python sites\\tenant_shop\\generate_readme.py",
        "```",
        "",
        "## 成果物",
        "",
        "```text",
        "output/tenant_shop/tenant_shop_detail.csv",
        "output/tenant_shop/tenant_shop.csv",
        "output/tenant_shop/tenant_shop_geocoded.csv",
        "output/tenant_shop/tenant_shop_geocode_failed.csv",
        "output/tenant_shop_map.html",
        "sites/tenant_shop/selectors.py",
        "sites/tenant_shop/README.md",
        "```",
        "",
        "## 備考",
        "",
        "- テナントショップで発見した高松市の物件1件を個別取得。",
        "- 一覧取得は行わず、詳細URLから直接取得。",
        "- ジオコード成功。",
        "",
    ]

    README_PATH.write_text(
        "\n".join(readme_lines),
        encoding="utf-8"
    )

    print(f"saved: {README_PATH}")


if __name__ == "__main__":
    main()