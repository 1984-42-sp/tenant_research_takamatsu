from pathlib import Path
from urllib.parse import urljoin
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.takamatsuhousing.jp"
HTML_DIR = Path("data/html/takamatsu_housing")
DETAIL_DIR = HTML_DIR / "detail"

DETAIL_DIR.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

detail_urls = []

for page in range(1, 5):

    path = HTML_DIR / f"list_page_{page}.html"

    html = path.read_text(
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/kasi-tenpo/detail-" in href:
            detail_urls.append(
                urljoin(BASE_URL, href)
            )

detail_urls = sorted(set(detail_urls))

print("detail urls:", len(detail_urls))

for i, url in enumerate(detail_urls, start=1):

    article_id = (
        url.rstrip("/")
        .split("/")[-1]
        .replace("detail-", "")
    )

    path = DETAIL_DIR / f"{article_id}.html"

    if path.exists():
        print(f"skip {i}/{len(detail_urls)} {path.name}")
        continue

    print(f"fetch {i}/{len(detail_urls)} {url}")

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    path.write_text(
        response.text,
        encoding="utf-8"
    )

    time.sleep(1)

print("done")