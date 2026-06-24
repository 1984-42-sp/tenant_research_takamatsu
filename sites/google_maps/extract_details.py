from pathlib import Path
import re
from urllib.parse import urlparse, unquote
import pandas as pd
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[2]

MANIFEST_PATH = BASE_DIR / "data" / "html" / "google_maps" / "details_manifest.csv"
OUT_DIR = BASE_DIR / "output" / "google_maps"
OUT_PATH = OUT_DIR / "google_maps_cafes_from_details.csv"

COLUMNS = [
    "competitor_id",
    "store_name",
    "source",
    "genre",
    "address",
    "lat",
    "lng",
    "rating",
    "review_count",
    "business_hours",
    "closed_days",
    "url",
    "linked_site_name",
    "linked_url",
    "memo",
]


def classify_site_name(url: str) -> str:
    netloc = urlparse(url).netloc.lower()

    if "tabelog.com" in netloc:
        return "食べログ"
    if "hotpepper.jp" in netloc:
        return "ホットペッパーグルメ"
    if "instagram.com" in netloc:
        return "Instagram"
    if "facebook.com" in netloc:
        return "Facebook"
    if "retty.me" in netloc:
        return "Retty"
    if "gnavi.co.jp" in netloc:
        return "ぐるなび"
    if "tripadvisor." in netloc:
        return "Tripadvisor"

    return "公式サイト候補"


def is_valid_linked_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False

    netloc = urlparse(url).netloc.lower()

    ignore = [
        "google.com",
        "google.co.jp",
        "gstatic.com",
        "googleusercontent.com",
        "googleapis.com",
        "schema.org",
        "ggpht.com",
        "apache.org",
    ]

    return not any(x in netloc for x in ignore)


def clean_url(url: str) -> str:
    return unquote(url).strip().rstrip("),.;]")


def extract_linked_url_from_website_button(soup: BeautifulSoup):
    # Google Maps詳細パネルの「ウェブサイト」ボタン周辺だけを見る
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        aria = a.get("aria-label", "")
        title = a.get("title", "")

        label = f"{text} {aria} {title}"

        if "ウェブサイト" not in label and "Website" not in label:
            continue

        href = clean_url(a.get("href", ""))

        if is_valid_linked_url(href):
            return classify_site_name(href), href

    return "", ""


def extract_rating_review(text: str):
    m = re.search(r"([0-5]\.\d)\s*\((\d{1,6})\)", text)
    if m:
        return m.group(1), m.group(2)
    return "", ""


def extract_coord_from_url(url: str):
    if not isinstance(url, str):
        return "", ""

    matches = re.findall(r"!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if matches:
        lat, lng = matches[-1]
        return lat, lng

    matches = re.findall(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if matches:
        lat, lng = matches[-1]
        return lat, lng

    return "", ""


def extract_address(text: str):
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    for line in lines:
        if "香川県高松市" in line:
            return line

    for line in lines:
        if "高松市" in line:
            return "香川県" + line

    return ""


def extract_genre(text: str):
    keywords = ["カフェ", "喫茶", "コーヒー", "スイーツ", "ベーカリー"]
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    for line in lines:
        if any(k in line for k in keywords) and len(line) <= 30:
            return line

    return ""


def extract_business_hours(text: str):
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    for line in lines:
        if "営業開始" in line or "営業終了" in line or "営業時間" in line:
            return line.replace("·", "").strip()

    return ""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(MANIFEST_PATH)

    rows = []

    for _, row in manifest.iterrows():
        store_name = str(row.get("store_name", "")).strip()

        if store_name in {"結果", "Google マップ", "Google Maps"}:
            continue

        detail_html_rel = str(row.get("detail_html", "")).strip()
        google_maps_url = str(row.get("google_maps_url", "")).strip()

        html_path = BASE_DIR / detail_html_rel

        if not html_path.exists():
            print(f"[WARN] HTMLなし: {html_path}")
            continue

        raw_html = html_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text("\n", strip=True)

        rating, review_count = extract_rating_review(text)
        lat, lng = extract_coord_from_url(google_maps_url)
        linked_site_name, linked_url = extract_linked_url_from_website_button(soup)

        rows.append(
            {
                "competitor_id": f"GMP{len(rows) + 1:05d}",
                "store_name": store_name,
                "source": "google_maps",
                "genre": extract_genre(text),
                "address": extract_address(text),
                "lat": lat,
                "lng": lng,
                "rating": rating,
                "review_count": review_count,
                "business_hours": extract_business_hours(text),
                "closed_days": "",
                "url": google_maps_url,
                "linked_site_name": linked_site_name,
                "linked_url": linked_url,
                "memo": "",
            }
        )

    df = pd.DataFrame(rows, columns=COLUMNS)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {OUT_PATH}")
    print(f"[ROWS] {len(df)}")
    print(f"[UNIQUE] {df['store_name'].nunique()}")

    print("\n=== linked_url count ===")
    print(df["linked_url"].astype(str).str.len().gt(0).sum())

    print("\n=== preview ===")
    print(df[["store_name", "linked_site_name", "linked_url"]].head(20))


if __name__ == "__main__":
    main()