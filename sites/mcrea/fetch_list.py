from pathlib import Path
import time

import requests

import selectors

OUT_DIR = Path("data/html/mcrea")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Connection": "close",
}


def fetch_with_retry(url: str, retry: int = 5) -> str:
    last_error = None

    for attempt in range(1, retry + 1):
        print(f"  attempt {attempt}/{retry}")

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=(20, 120),
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text

        except Exception as e:
            last_error = e
            print(f"  [retry] {repr(e)}")
            time.sleep(10 * attempt)

    raise last_error


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for item in selectors.LIST_URLS:
        page_no = item["page"]
        url = item["url"]
        out_path = OUT_DIR / f"list_page_{page_no}.html"

        if out_path.exists():
            print(f"[skip] already exists: {out_path}")
            continue

        print(f"[fetch] page {page_no}: {url}")

        html = fetch_with_retry(url)

        out_path.write_text(html, encoding="utf-8")

        print(f"[saved] {out_path}")
        print(f"[size] {len(html)}")

        time.sleep(15)


if __name__ == "__main__":
    main()