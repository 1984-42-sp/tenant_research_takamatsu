from pathlib import Path
import importlib.util
import re

import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path,
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

DETAIL_DIR = ROOT / "data" / "html" / selectors.SITE_NAME / "detail"
OUTPUT_DIR = ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / selectors.OUTPUT_DETAIL_CSV


def clean(text):
    return " ".join(str(text).split())


def extract_id_from_filename(filename):
    return Path(filename).stem


def normalize_key(key):
    return clean(key).replace(" /", "/").replace("/ ", "/")


def extract_article_id_from_url_or_file(html_path):
    return html_path.stem


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_files = sorted(DETAIL_DIR.glob("*.html"))
    rows = []

    for html_path in html_files:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

        row = {
            "article_id": extract_article_id_from_url_or_file(html_path),
            "source_file": html_path.name,
            "site": selectors.SITE_LABEL,
            "detail_url": f"{selectors.BASE_URL}/kasi-tenpo/detail-{html_path.stem}/",
        }

        h1 = soup.select_one("h1")
        row["title"] = clean(h1.get_text(" ", strip=True)) if h1 else ""

        for table in soup.select("table"):
            for tr in table.select("tr"):
                ths = tr.select("th")
                tds = tr.select("td")

                if not ths or not tds:
                    continue

                for i, th in enumerate(ths):
                    key = normalize_key(th.get_text(" ", strip=True))

                    if not key:
                        continue

                    value = clean(tds[i].get_text(" ", strip=True)) if i < len(tds) else ""

                    if not value:
                        continue

                    if key not in row:
                        row[key] = value

        # 飲食店可否判定
        tokki = row.get("特記事項", "")
        title = row.get("title", "")
        text_all = " ".join([tokki, title, row.get("設備", ""), row.get("備考", "")])

        if "飲食店不可" in text_all:
            row["飲食店可否"] = "不可"
        elif "飲食店可" in text_all:
            row["飲食店可否"] = "可"
        else:
            row["飲食店可否"] = "不明"

        rows.append(row)

    df = pd.DataFrame(rows)

    print("==== EXTRACT DETAIL ====")
    print(f"rows: {len(df)}")
    print(f"expected: {selectors.EXPECTED_LIST_COUNT}")

    if len(df) != selectors.EXPECTED_LIST_COUNT:
        print("WARNING: detail rows count does not match expected count")

    key_columns = [
        "article_id",
        "title",
        "所在地",
        "賃料",
        "使用部分面積",
        "建物名・部屋番号",
        "物件種目",
        "特記事項",
        "飲食店可否",
    ]

    existing_columns = [col for col in key_columns if col in df.columns]
    print()
    print(df[existing_columns])

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print()
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()