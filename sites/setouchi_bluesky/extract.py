from pathlib import Path
from urllib.parse import urljoin
import importlib.util
import re

import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

HTML_PATH = ROOT / "data" / "html" / selectors.SITE_NAME / selectors.HTML_LIST_FILENAME
OUTPUT_DIR = ROOT / "output" / selectors.SITE_NAME
OUTPUT_PATH = OUTPUT_DIR / selectors.OUTPUT_LIST_CSV


def clean(text):
    return " ".join(str(text).split())


def find_parent_block(a_tag):
    current = a_tag

    for _ in range(8):
        current = current.parent

        if current is None:
            break

        detail_links = current.select(
            f'a[href*="{selectors.DETAIL_URL_KEYWORD}"]'
        )
        text = clean(current.get_text(" ", strip=True))

        if len(detail_links) >= 1 and len(text) >= 50:
            return current

    return a_tag.parent


def extract_label_value(text, label):
    pattern = rf"{label}\s*([^\s]+)"
    match = re.search(pattern, text)

    if match:
        return clean(match.group(1))

    return ""


def main():
    if not HTML_PATH.exists():
        raise FileNotFoundError(f"HTML not found: {HTML_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    soup = BeautifulSoup(HTML_PATH.read_text(encoding="utf-8"), "lxml")

    rows = []
    seen_urls = set()

    for a in soup.select(selectors.LIST_SELECTORS["detail_link"]):
        href = a.get("href")

        if not href:
            continue

        detail_url = urljoin(selectors.BASE_URL, href)

        if detail_url in seen_urls:
            continue

        seen_urls.add(detail_url)

        block = find_parent_block(a)
        block_text = clean(block.get_text(" ", strip=True))

        name_candidates = []

        for tag in block.select("h1, h2, h3, h4, .title, .name, dt, strong, b, a"):
            text = clean(tag.get_text(" ", strip=True))

            if not text:
                continue

            if text in selectors.EXCLUDE_KEYWORDS:
                continue

            if "物件詳細を見る" in text:
                continue

            if "お問い合わせ" in text:
                continue

            if len(text) <= 2:
                continue

            name_candidates.append(text)

        name = name_candidates[0] if name_candidates else ""

        rows.append(
            {
                "site": selectors.SITE_LABEL,
                "page_no": 1,
                "name": name,
                "detail_url": detail_url,
                "list_url": selectors.LIST_URL,
                "list_text": block_text,
                "rent": extract_label_value(block_text, "賃料"),
                "area": extract_label_value(block_text, "面積"),
            }
        )

    df = pd.DataFrame(rows)

    print("==== EXTRACT LIST ====")
    print(f"html: {HTML_PATH}")
    print(f"rows: {len(df)}")
    print(f"expected: {selectors.EXPECTED_LIST_COUNT}")

    if len(df) != selectors.EXPECTED_LIST_COUNT:
        print("WARNING: extracted rows count does not match expected count")

    print()
    print(df[["name", "detail_url"]])

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print()
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()