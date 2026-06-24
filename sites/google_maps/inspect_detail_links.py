from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[2]
MANIFEST_PATH = BASE_DIR / "data" / "html" / "google_maps" / "details_manifest.csv"


def main():
    manifest = pd.read_csv(MANIFEST_PATH)

    for _, row in manifest.iterrows():
        store_name = str(row.get("store_name", "")).strip()

        if store_name in {"結果", "Google マップ", "Google Maps"}:
            continue

        html_path = BASE_DIR / str(row.get("detail_html", "")).strip()

        if not html_path.exists():
            continue

        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")

        candidates = []

        for a in soup.find_all("a", href=True):
            text = a.get_text(" ", strip=True)
            aria = a.get("aria-label", "")
            title = a.get("title", "")
            href = a.get("href", "")

            label = f"{text} {aria} {title}"

            if "ウェブサイト" in label or "Website" in label:
                candidates.append((label.strip(), href))

        print("\n" + "=" * 80)
        print(store_name)
        print(html_path)

        if not candidates:
            print("[NO WEBSITE LINK]")
            continue

        for label, href in candidates:
            print("[LABEL]", label)
            print("[URL]  ", href)
            print("[HOST] ", urlparse(href).netloc)


if __name__ == "__main__":
    main()