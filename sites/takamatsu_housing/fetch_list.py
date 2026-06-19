from pathlib import Path
import time
import requests

BASE_URL = "https://www.takamatsuhousing.jp"
HTML_DIR = Path("data/html/takamatsu_housing")

HTML_DIR.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

for page in range(1, 5):

    if page == 1:
        url = (
            BASE_URL
            + "/kasi-tenpo/kagawa/result/takamatsu-city.html"
        )
    else:
        url = (
            BASE_URL
            + f"/kasi-tenpo/kagawa/result/takamatsu-city.html?page={page}"
        )

    print(f"fetch page {page}: {url}")

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    path = HTML_DIR / f"list_page_{page}.html"

    path.write_text(
        response.text,
        encoding="utf-8"
    )

    print(f"saved: {path}")

    time.sleep(1)