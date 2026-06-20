from pathlib import Path
from playwright.sync_api import sync_playwright
import selectors

OUT_DIR = Path("data/html/uemura_re")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for i, item in enumerate(selectors.LIST_URLS, start=1):
            url = item["url"]
            category = item["category"]

            print(f"[fetch] {category}: {url}")
            page.goto(url, wait_until="networkidle")

            html = page.content()
            out_path = OUT_DIR / f"list_page_{i}.html"
            out_path.write_text(html, encoding="utf-8")

            print(f"[saved] {out_path}")

        browser.close()


if __name__ == "__main__":
    main()