from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

import selectors

HTML_DIR = Path("data/html/mcrea")
OUT_PATH = Path("output/mcrea/mcrea_list.csv")


def main():
    rows = []
    seen_urls = set()

    for item in selectors.LIST_URLS:
        page_no = item["page"]
        list_url = item["url"]
        html_path = HTML_DIR / f"list_page_{page_no}.html"

        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

        for a in soup.select("p.object-name a[href*='detail']"):
            href = a.get("href")
            detail_url = urljoin(selectors.BASE_URL, href)
            name = a.get_text(" ", strip=True)

            if detail_url in seen_urls:
                continue

            seen_urls.add(detail_url)

            rows.append(
                {
                    "site": selectors.SITE_LABEL,
                    "category": "貸店舗",
                    "name": name,
                    "detail_url": detail_url,
                    "list_url": list_url,
                    "page_no": page_no,
                }
            )

    df = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"extracted: {len(df)}")
    print(f"expected : {selectors.EXPECTED_LIST_COUNT}")
    print(f"saved    : {OUT_PATH}")

    if len(df) != selectors.EXPECTED_LIST_COUNT:
        raise ValueError("一覧取得件数が想定件数と一致しません")


if __name__ == "__main__":
    main()