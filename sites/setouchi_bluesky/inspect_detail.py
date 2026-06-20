from pathlib import Path
import importlib.util

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path,
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

DETAIL_DIR = ROOT / "data" / "html" / selectors.SITE_NAME / "detail"


def clean(text):
    return " ".join(str(text).split())


def main():
    html_files = sorted(DETAIL_DIR.glob("*.html"))

    print("==== INSPECT DETAIL ====")
    print(f"detail html count: {len(html_files)}")
    print(f"expected: {selectors.EXPECTED_LIST_COUNT}")
    print()

    for html_path in html_files:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

        print("=" * 100)
        print(html_path.name)
        print("=" * 100)

        title = ""
        h1 = soup.select_one("h1")
        if h1:
            title = clean(h1.get_text(" ", strip=True))

        print(f"title: {title}")
        print()

        for table in soup.select("table"):
            for tr in table.select("tr"):
                ths = tr.select("th")
                tds = tr.select("td")

                if not ths or not tds:
                    continue

                for i, th in enumerate(ths):
                    key = clean(th.get_text(" ", strip=True))

                    if i < len(tds):
                        value = clean(tds[i].get_text(" ", strip=True))
                    else:
                        value = ""

                    if key or value:
                        print(f"{key}: {value}")

        print()


if __name__ == "__main__":
    main()