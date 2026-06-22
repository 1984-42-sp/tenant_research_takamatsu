from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from playwright.sync_api import sync_playwright

import selectors

LIST_CSV = Path(
    "output/uemura_re/uemura_re_list.csv"
)
OUT_DIR = Path(
    "data/html/uemura_re/detail"
)


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.replace("/", "_")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(LIST_CSV)

    urls = []

    for _, row in df.iterrows():
        urls.append(
            {
                "category": row["category"],
                "url": row["detail_url"],
            }
        )

    urls.extend(selectors.EXTRA_DETAIL_URLS)

    print(f"detail urls: {len(urls)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for i, item in enumerate(urls, start=1):
            url = item["url"]
            category = item["category"]
            slug = slug_from_url(url)
            out_path = OUT_DIR / f"{slug}.html"

            print(f"[{i}/{len(urls)}] {category}: {url}")
            page.goto(url, wait_until="networkidle")

            html = page.content()
            out_path.write_text(html, encoding="utf-8")

            print(f"[saved] {out_path}")

        browser.close()


if __name__ == "__main__":
    main()