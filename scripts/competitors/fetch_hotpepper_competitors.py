from pathlib import Path
import os
import time
import requests
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

OUT_PATH = BASE_DIR / "data" / "competitors" / "raw" / "hotpepper_competitors.csv"

API_URL = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

# 高松市をざっくり面で拾うための検索中心点
SEARCH_POINTS = [
    ("高松中心部", 34.342787, 134.046574),
    ("瓦町・常磐町", 34.338900, 134.052800),
    ("北浜・サンポート", 34.352900, 134.046300),
    ("栗林・三条", 34.323600, 134.048600),
    ("木太町", 34.318900, 134.077000),
    ("屋島", 34.336500, 134.101000),
    ("仏生山", 34.283700, 134.045700),
    ("国分寺", 34.304300, 133.956700),
]

KEYWORDS = [
    "カフェ",
    "喫茶",
    "コーヒー",
]

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


def fetch(api_key, area_name, lat, lng, keyword):
    params = {
        "key": api_key,
        "lat": lat,
        "lng": lng,
        "range": 5,
        "keyword": keyword,
        "count": 100,
        "format": "json",
    }

    res = requests.get(API_URL, params=params, timeout=20)
    res.raise_for_status()
    data = res.json()

    shops = data.get("results", {}).get("shop", [])
    records = []

    for shop in shops:
        genre = shop.get("genre", {}) or {}
        urls = shop.get("urls", {}) or {}

        records.append(
            {
                "competitor_id": "",
                "store_name": shop.get("name", ""),
                "source": "hotpepper",
                "genre": genre.get("name", ""),
                "address": shop.get("address", ""),
                "lat": shop.get("lat", ""),
                "lng": shop.get("lng", ""),
                "rating": "",
                "review_count": "",
                "business_hours": shop.get("open", ""),
                "closed_days": shop.get("close", ""),
                "url": urls.get("pc", ""),
                "memo": f"search_area={area_name}; keyword={keyword}",
            }
        )

    return records


def main():
    api_key = os.getenv("HOTPEPPER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "環境変数 HOTPEPPER_API_KEY が未設定です。"
            'PowerShellで $env:HOTPEPPER_API_KEY="あなたのAPIキー" を実行してください。'
        )

    all_records = []

    for area_name, lat, lng in SEARCH_POINTS:
        for keyword in KEYWORDS:
            print(f"[FETCH] {area_name} / {keyword}")

            records = fetch(api_key, area_name, lat, lng, keyword)
            print(f"  -> {len(records)} rows")

            all_records.extend(records)
            time.sleep(1)

    df = pd.DataFrame(all_records, columns=COLUMNS)

    if not df.empty:
        df = df.drop_duplicates(
            subset=["store_name", "address", "source"],
            keep="first",
        ).reset_index(drop=True)

        df["competitor_id"] = [
            f"HP{i + 1:05d}" for i in range(len(df))
        ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {OUT_PATH}: {len(df)} rows")


if __name__ == "__main__":
    main()