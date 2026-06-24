from pathlib import Path
import csv
import html as html_lib
import re
from urllib.parse import parse_qs, unquote, urlparse
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[2]
HTML_PATH = BASE_DIR / "data" / "html" / "google_maps" / "search_result.html"
OUT_DIR = BASE_DIR / "output" / "google_maps"
OUT_PATH = OUT_DIR / "google_maps_cafes.csv"

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

GENRE_KEYWORDS = ["カフェ", "喫茶", "コーヒー", "スイーツ", "ベーカリー"]

SKIP_LINES = {
    "共有",
    "結果",
    "価格",
    "評価",
    "時間",
    "すべてのフィルタ",
    "営業時間外",
    "オンラインで注文",
}


def is_rating(line: str) -> bool:
    return bool(re.fullmatch(r"[0-5]\.\d", line))


def is_review_count(line: str) -> bool:
    return bool(re.fullmatch(r"\(\d{1,5}\)", line))


def is_genre(line: str) -> bool:
    return any(k in line for k in GENRE_KEYWORDS)


def clean_review_count(line: str) -> str:
    return line.replace("(", "").replace(")", "")


def clean_line(line: str) -> str:
    return line.strip().replace("\u3000", " ")


def normalize_address(address: str) -> str:
    if not address:
        return ""
    address = address.strip()
    if address.startswith("香川県"):
        return address
    if address.startswith("高松市"):
        return "香川県" + address
    return "香川県高松市" + address


def clean_business_hours(value: str) -> str:
    return value.replace("·", "").strip()


def normalize_url(url: str) -> str:
    if not url:
        return ""

    url = html_lib.unescape(unquote(url.strip()))

    parsed = urlparse(url)

    if "google." in parsed.netloc and parsed.path.startswith("/url"):
        qs = parse_qs(parsed.query)
        if "q" in qs:
            return qs["q"][0]
        if "url" in qs:
            return qs["url"][0]

    return url


def classify_site_name(url: str) -> str:
    if not url:
        return ""

    netloc = urlparse(url).netloc.lower()

    if "tabelog.com" in netloc:
        return "食べログ"
    if "hotpepper.jp" in netloc:
        return "ホットペッパーグルメ"
    if "instagram.com" in netloc:
        return "Instagram"
    if "facebook.com" in netloc:
        return "Facebook"
    if "x.com" in netloc or "twitter.com" in netloc:
        return "X"
    if "google." in netloc:
        return "Google Maps"
    if "retty.me" in netloc:
        return "Retty"
    if "tripadvisor." in netloc:
        return "Tripadvisor"
    if "gnavi.co.jp" in netloc:
        return "ぐるなび"
    if "r.gnavi.co.jp" in netloc:
        return "ぐるなび"

    return "公式サイト候補"


def is_external_candidate(url: str) -> bool:
    if not url.startswith("http"):
        return False

    netloc = urlparse(url).netloc.lower()

    ignore_domains = [
        "google.com",
        "google.co.jp",
        "gstatic.com",
        "googleusercontent.com",
        "schema.org",
    ]

    return not any(domain in netloc for domain in ignore_domains)


def extract_google_maps_url(soup: BeautifulSoup, store_name: str) -> str:
    for a in soup.find_all("a", href=True):
        label = " ".join(
            [
                a.get_text(" ", strip=True),
                a.get("aria-label", ""),
                a.get("title", ""),
            ]
        )

        href = normalize_url(a["href"])

        if store_name in label and ("google.com/maps" in href or "google.co.jp/maps" in href):
            return href

    return ""


def extract_linked_url(raw_html: str, store_name: str) -> tuple[str, str]:
    pos = raw_html.find(store_name)
    if pos == -1:
        return "", ""

    window = raw_html[max(0, pos - 4000) : pos + 12000]
    window = html_lib.unescape(unquote(window))

    urls = re.findall(r"https?://[^\s\"'<>\\]+", window)

    for url in urls:
        url = normalize_url(url)
        if is_external_candidate(url):
            return classify_site_name(url), url

    return "", ""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_html = HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw_html, "html.parser")

    text = soup.get_text("\n", strip=True)
    lines = [clean_line(x) for x in text.splitlines()]
    lines = [x for x in lines if x and x not in SKIP_LINES]

    rows = []
    seen = set()

    for i, line in enumerate(lines):
        if not is_rating(line):
            continue

        store_name = lines[i - 1] if i > 0 else ""
        rating = line
        review_count = ""
        genre = ""
        address = ""
        business_hours = ""

        if store_name in seen:
            continue

        if i + 1 < len(lines) and is_review_count(lines[i + 1]):
            review_count = clean_review_count(lines[i + 1])

        window = lines[i + 1 : i + 18]

        for w in window:
            if not genre and is_genre(w):
                genre = w
                continue

            if not business_hours and ("営業開始" in w or "営業終了" in w or "営業中" in w):
                business_hours = w
                continue

            if genre and not address:
                if (
                    "町" in w
                    or "丁目" in w
                    or "番地" in w
                    or "F" in w
                    or "階" in w
                    or "−" in w
                    or "-" in w
                ):
                    if not is_genre(w) and not is_review_count(w) and not is_rating(w):
                        address = w
                        continue

        if not store_name or len(store_name) <= 1:
            continue

        if any(x in store_name for x in ["Google", "検索", "フィルタ", "サイドパネル"]):
            continue

        seen.add(store_name)

        google_maps_url = extract_google_maps_url(soup, store_name)
        linked_site_name, linked_url = extract_linked_url(raw_html, store_name)

        rows.append(
            {
                "competitor_id": f"GMP{len(rows) + 1:05d}",
                "store_name": store_name,
                "source": "google_maps",
                "genre": genre,
                "address": normalize_address(address),
                "lat": "",
                "lng": "",
                "rating": rating,
                "review_count": review_count,
                "business_hours": clean_business_hours(business_hours),
                "closed_days": "",
                "url": google_maps_url,
                "linked_site_name": linked_site_name,
                "linked_url": linked_url,
                "memo": "",
            }
        )

    with OUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[SAVE] {OUT_PATH}")
    print(f"[ROWS] {len(rows)}")

    print("\n=== preview ===")
    for row in rows[:10]:
        print(row)


if __name__ == "__main__":
    main()