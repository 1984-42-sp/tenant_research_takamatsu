from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API_URL = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

MIDDLE_AREAS = ["Y650", "Y652"]
GENRE = "G014"

OUT_CSV = Path("data/competitors/raw/hotpepper_cafe_competitors.csv")

COUNT = 100
SLEEP_SECONDS = 1.0


def get_nested(obj: dict[str, Any], *keys: str) -> str:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(key)
    return "" if cur is None else str(cur)


def is_cafe_like(shop: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(shop.get("name", "")),
            get_nested(shop, "genre", "name"),
            get_nested(shop, "genre", "catch"),
            get_nested(shop, "sub_genre", "name"),
            str(shop.get("catch", "")),
            str(shop.get("open", "")),
            str(shop.get("access", "")),
        ]
    ).lower()

    include_words = [
        "カフェ",
        "cafe",
        "喫茶",
        "珈琲",
        "コーヒー",
        "coffee",
        "ブックカフェ",
        "スイーツ",
        "クレープ",
        "バーガー",
    ]

    return any(word.lower() in text for word in include_words)


def fetch_page(api_key: str, middle_area: str, start: int) -> dict[str, Any]:
    params = {
        "key": api_key,
        "middle_area": middle_area,
       # "genre": GENRE,
        "format": "json",
        "count": COUNT,
        "start": start,
    }

    res = requests.get(API_URL, params=params, timeout=30)
    res.raise_for_status()

    data = res.json()
    results = data.get("results", {})

    if "error" in results:
        raise RuntimeError(results["error"])

    return results


def flatten_shop(shop: dict[str, Any], middle_area_query: str) -> dict[str, Any]:
    hotpepper_id = str(shop.get("id", "")).strip()

    memo_parts = [
        f"hotpepper_id={hotpepper_id}",
        f"name_kana={shop.get('name_kana', '')}",
        f"station_name={shop.get('station_name', '')}",
        f"access={shop.get('access', '')}",
        f"budget={get_nested(shop, 'budget', 'name')}",
        f"parking={shop.get('parking', '')}",
        f"wifi={shop.get('wifi', '')}",
        f"card={shop.get('card', '')}",
        f"non_smoking={shop.get('non_smoking', '')}",
        f"middle_area_query={middle_area_query}",
        f"middle_area_code={get_nested(shop, 'middle_area', 'code')}",
        f"middle_area_name={get_nested(shop, 'middle_area', 'name')}",
        f"small_area_code={get_nested(shop, 'small_area', 'code')}",
        f"small_area_name={get_nested(shop, 'small_area', 'name')}",
        f"lat={shop.get('lat', '')}",
        f"lng={shop.get('lng', '')}",
        f"photo_url={get_nested(shop, 'photo', 'pc', 'l')}",
        f"catch={shop.get('catch', '')}",
        f"genre_catch={get_nested(shop, 'genre', 'catch')}",
    ]

    return {
        "competitor_id": f"hotpepper_{hotpepper_id}",
        "store_name": shop.get("name", ""),
        "source": "hotpepper",
        "genre": get_nested(shop, "genre", "name"),
        "address": shop.get("address", ""),
        "rating": "",
        "review_count": "",
        "business_hours": shop.get("open", ""),
        "closed_days": shop.get("close", ""),
        "url": get_nested(shop, "urls", "pc"),
        "memo": " | ".join(memo_parts),
    }


def main() -> None:
    api_key = os.environ.get("HOTPEPPER_API_KEY")
    if not api_key:
        raise SystemExit("環境変数 HOTPEPPER_API_KEY が未設定です。")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for middle_area in MIDDLE_AREAS:
        print(f"[FETCH] middle_area={middle_area}")

        start = 1

        while True:
            results = fetch_page(api_key, middle_area, start)

            available = int(results.get("results_available", 0))
            returned = int(results.get("results_returned", 0))
            shops = results.get("shop", [])

            if isinstance(shops, dict):
                shops = [shops]

            print(
                f"  start={start} available={available} returned={returned} shops={len(shops)}"
            )

            if not shops:
                break

            for shop in shops:
                hotpepper_id = str(shop.get("id", "")).strip()

                if not hotpepper_id:
                    continue

                if hotpepper_id in seen_ids:
                    continue

                if not is_cafe_like(shop):
                    continue

                rows.append(flatten_shop(shop, middle_area))
                seen_ids.add(hotpepper_id)

            next_start = start + returned

            if returned <= 0 or next_start > available:
                break

            start = next_start
            time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(rows)

    columns = [
        "competitor_id",
        "store_name",
        "source",
        "genre",
        "address",
        "rating",
        "review_count",
        "business_hours",
        "closed_days",
        "url",
        "memo",
    ]

    df = df.reindex(columns=columns)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {OUT_CSV} rows={len(df)} cols={len(df.columns)}")


if __name__ == "__main__":
    main()