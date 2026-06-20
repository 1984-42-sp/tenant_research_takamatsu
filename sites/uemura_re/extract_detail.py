from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

import selectors

DETAIL_DIR = Path("data/html/uemura_re/detail")
OUT_PATH = Path("output/uemura_re_detail.csv")


def normalize_key(text: str) -> str:
    return text.replace(" ", "").replace("　", "").strip()


def extract_pairs_from_tr(tr):
    cells = [c.get_text(" ", strip=True) for c in tr.select("th, td")]
    cells = [c for c in cells if c != ""]

    pairs = []
    if len(cells) >= 2:
        for i in range(0, len(cells) - 1, 2):
            key = normalize_key(cells[i])
            value = cells[i + 1].strip()
            if key:
                pairs.append((key, value))
    return pairs


def category_from_path(path: Path) -> str:
    name = path.name
    if name.startswith("kasi-other"):
        return "貸ビル・貸倉庫・その他"
    return "貸店舗"


def detail_url_from_path(path: Path) -> str:
    stem = path.stem
    if stem.startswith("kasi-other_"):
        url_path = stem.replace("_", "/", 1)
    elif stem.startswith("kasi-tenpo_"):
        url_path = stem.replace("_", "/", 1)
    else:
        url_path = stem.replace("_", "/")
    return urljoin(selectors.BASE_URL, f"/{url_path}/")


def main():
    rows = []

    files = sorted(DETAIL_DIR.glob("*.html"))
    print(f"files: {len(files)}")

    for path in files:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

        row = {
            "site": selectors.SITE_LABEL,
            "category": category_from_path(path),
            "detail_url": detail_url_from_path(path),
            "html_file": str(path),
        }

        h2 = soup.select_one("h2.article-heading")
        if h2:
            row["物件名"] = h2.get_text(" ", strip=True)

        h1 = soup.select_one("h1")
        if h1:
            row["ページ見出し"] = h1.get_text(" ", strip=True)

        for tr in soup.select("tr"):
            for key, value in extract_pairs_from_tr(tr):
                if key in selectors.EXCLUDE_KEYWORDS:
                    continue

                if key in row and row[key] != value:
                    row[f"{key}_2"] = value
                else:
                    row[key] = value

        rows.append(row)

    df = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"extracted: {len(df)}")
    print(f"expected : {selectors.EXPECTED_TOTAL_COUNT}")
    print(f"saved    : {OUT_PATH}")
    print(f"columns  : {len(df.columns)}")

    if len(df) != selectors.EXPECTED_TOTAL_COUNT:
        raise ValueError("詳細取得件数が想定件数と一致しません")


if __name__ == "__main__":
    main()