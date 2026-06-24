from pathlib import Path
import csv
import re
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
    "memo",
]

GENRE_KEYWORDS = [
    "カフェ",
    "喫茶",
    "コーヒー",
    "スイーツ",
    "ベーカリー",
]

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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    html = HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

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

        # rating の次に口コミ数が来る想定
        if i + 1 < len(lines) and is_review_count(lines[i + 1]):
            review_count = clean_review_count(lines[i + 1])

        # rating以降15行程度からジャンル・住所・営業時間を拾う
        window = lines[i + 1 : i + 18]

        for w in window:
            if not genre and is_genre(w):
                genre = w
                continue

            if not business_hours and ("営業開始" in w or "営業終了" in w or "営業中" in w):
                business_hours = w
                continue

            # 住所候補: ジャンル取得後に出てくる、日本語住所っぽい行
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

        # 明らかなUI文言を除外
        if any(x in store_name for x in ["Google", "検索", "フィルタ", "サイドパネル"]):
            continue

        seen.add(store_name)

        rows.append(
            {
                "competitor_id": f"GMP{len(rows) + 1:05d}",
                "store_name": store_name,
                "source": "google_maps",
                "genre": genre,
                "address": address,
                "lat": "",
                "lng": "",
                "rating": rating,
                "review_count": review_count,
                "business_hours": business_hours,
                "closed_days": "",
                "url": "",
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