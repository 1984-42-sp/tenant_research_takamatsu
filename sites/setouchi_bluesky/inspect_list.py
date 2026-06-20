from pathlib import Path
from urllib.parse import urljoin
import importlib.util

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location("setouchi_bluesky_selectors", selectors_path)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

HTML_PATH = ROOT / "data" / "html" / selectors.SITE_NAME / "list_page_1.html"


def clean(text):
    return " ".join(text.split())


def main():
    if not HTML_PATH.exists():
        raise FileNotFoundError(f"HTML not found: {HTML_PATH}")

    soup = BeautifulSoup(HTML_PATH.read_text(encoding="utf-8"), "lxml")

    links = []

    for a in soup.select(f'a[href*="{selectors.DETAIL_URL_KEYWORD}"]'):
        href = a.get("href")
        title = clean(a.get_text(" ", strip=True))

        if href:
            links.append({
                "title": title,
                "url": urljoin(selectors.BASE_URL, href),
            })

    unique = {}

    for item in links:
        unique[item["url"]] = item

    print("==== LIST INSPECT ====")
    print(f"html: {HTML_PATH}")
    print(f"detail links raw: {len(links)}")
    print(f"detail links unique: {len(unique)}")
    print(f"expected count: {selectors.EXPECTED_LIST_COUNT}")
    print()

    for i, item in enumerate(unique.values(), start=1):
        print(f"[{i}] {item['title']}")
        print(item["url"])
        print("-" * 80)

    print()
    print("==== COUNT TEXT CANDIDATES ====")

    for text in soup.stripped_strings:
        if "件中" in text and "件を表示" in text:
            print(text)


if __name__ == "__main__":
    main()