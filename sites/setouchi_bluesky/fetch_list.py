from pathlib import Path
from urllib.parse import urljoin
import importlib.util

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location("setouchi_bluesky_selectors", selectors_path)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

HTML_DIR = ROOT / "data" / "html" / selectors.SITE_NAME
HTML_PATH = HTML_DIR / "list_page_1.html"


def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(selectors.LIST_URL, wait_until="networkidle")
        page.wait_for_load_state("networkidle")

        HTML_PATH.write_text(page.content(), encoding="utf-8")

        links = page.locator(f'a[href*="{selectors.DETAIL_URL_KEYWORD}"]')
        hrefs = []

        for i in range(links.count()):
            href = links.nth(i).get_attribute("href")
            if href:
                hrefs.append(urljoin(selectors.BASE_URL, href))

        unique_hrefs = sorted(set(hrefs))

        print(f"saved: {HTML_PATH}")
        print(f"detail link count raw: {len(hrefs)}")
        print(f"detail link count unique: {len(unique_hrefs)}")
        print(f"expected count: {selectors.EXPECTED_LIST_COUNT}")

        for url in unique_hrefs:
            print(url)

        browser.close()


if __name__ == "__main__":
    main()