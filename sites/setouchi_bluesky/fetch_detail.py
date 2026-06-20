from pathlib import Path
import importlib.util
import re
import time

import pandas as pd
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

LIST_CSV_PATH = ROOT / "output" / selectors.OUTPUT_LIST_CSV
DETAIL_HTML_DIR = ROOT / "data" / "html" / selectors.SITE_NAME / "detail"


def safe_filename(url):
    match = re.search(r"detail-([^/]+)/?", url)

    if match:
        return f"{match.group(1)}.html"

    return re.sub(r"[^a-zA-Z0-9_-]", "_", url) + ".html"


def main():
    if not LIST_CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {LIST_CSV_PATH}")

    DETAIL_HTML_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(LIST_CSV_PATH)

    if "detail_url" not in df.columns:
        raise ValueError("detail_url column not found")

    urls = df["detail_url"].dropna().drop_duplicates().tolist()

    print("==== FETCH DETAIL ====")
    print(f"urls: {len(urls)}")
    print(f"expected: {selectors.EXPECTED_LIST_COUNT}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for i, url in enumerate(urls, start=1):
            filename = safe_filename(url)
            html_path = DETAIL_HTML_DIR / filename

            print(f"[{i}/{len(urls)}] {url}")
            page.goto(url, wait_until="networkidle")
            page.wait_for_load_state("networkidle")

            html_path.write_text(page.content(), encoding="utf-8")
            print(f"saved: {html_path}")

            time.sleep(1)

        browser.close()

    saved_files = list(DETAIL_HTML_DIR.glob("*.html"))

    print()
    print(f"saved html count: {len(saved_files)}")


if __name__ == "__main__":
    main()