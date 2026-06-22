from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://www.takamatsuhousing.jp"
HTML_DIR = Path("data/html/takamatsu_housing")
OUTPUT_PATH = Path("output/takamatsu_housing/takamatsu_housing_list.csv")

records = []

for page_no in range(1, 5):

    path = HTML_DIR / f"list_page_{page_no}.html"

    html = path.read_text(
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    blocks = soup.select(
        "div.article-object.kasi-tenpo"
    )

    print(
        f"page {page_no}: {len(blocks)}"
    )

    for block in blocks:

        link = block.select_one(
            'a[href*="/kasi-tenpo/detail-"]'
        )

        if link is None:
            continue

        href = link["href"]

        detail_url = urljoin(
            BASE_URL,
            href
        )

        article_id = (
            detail_url.rstrip("/")
            .split("/")[-1]
            .replace("detail-", "")
        )

        name = link.get_text(
            " ",
            strip=True
        )

        text = block.get_text(
            " ",
            strip=True
        )

        record = {
            "article_id": article_id,
            "name": name,
            "detail_url": detail_url,
            "page_no": page_no,
            "source_site": "takamatsu_housing",
            "list_text": text,
        }

        records.append(record)

df = pd.DataFrame(records)

print()
print(df.shape)

print()
print(
    df["article_id"]
    .duplicated()
    .sum()
)

df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print()
print(f"saved: {OUTPUT_PATH}")