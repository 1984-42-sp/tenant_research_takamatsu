from __future__ import annotations

"""
Hot Pepper Gourmet API fetcher for Takamatsu cafe competitors.

使い方:
  1) リクルートWEBサービスでAPIキーを取得
  2) PowerShell:
       $env:HOTPEPPER_API_KEY="取得したAPIキー"
       python scripts\competitors\fetch_hotpepper_cafes.py

出力:
  output\competitors\hotpepper_cafe_competitors.csv
"""

import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API_URL = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

# ホットペッパーWebの高松市中心部/郊外に対応する中エリアコード
MIDDLE_AREAS = ["Y650", "Y652"]

# G014 = カフェ・スイーツ
GENRE = "G014"

OUT_CSV = Path("output/competitors/hotpepper_cafe_competitors.csv")
COUNT = 100
SLEEP_SECONDS = 1.0


def get_nested(obj: dict[str, Any], *keys: str) -> str:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(key)
    if cur is None:
        return ""
    return str(cur)


def is_cafe_like(shop: dict[str, Any]) -> bool:
    """
    APIではWeb画面の /g140（カフェ小分類）を直接指定できない可能性が高いので、
    G014（カフェ・スイーツ）+ キーワード検索後にカフェ寄りの店舗を残す。
    """
    text = " ".join(
        [
            str(shop.get("name", "")),
            get_nested(shop, "genre", "name"),
            get_nested(shop, "genre", "catch"),
            get_nested(shop, "sub_genre", "name"),
            str(shop.get("catch", "")),
            str(shop.get("open", "")),
        ]
    ).lower()

    include_words = ["カフェ", "cafe", "喫茶", "珈琲", "コーヒー", "coffee"]
    return any(word.lower() in text for word in include_words)


def fetch_page(api_key: str, middle_area: str, start: int) -> dict[str, Any]:
    params = {
        "key": api_key,
        "middle_area": middle_area,
        "genre": GENRE,
        "keyword": "カフェ",
        "format": "json",
        "count": COUNT,
        "start": start,
    }
    res = requests.get(API_URL, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()
    if "error" in data.get("results", {}):
        raise RuntimeError(data["results"]["error"])
    return data["results"]


def flatten_shop(shop: dict[str, Any], middle_area_query: str) -> dict[str, Any]:
    return {
        "store_name": shop.get("name", ""),
        "source": "hotpepper",
        "genre": get_nested(shop, "genre", "name"),
        "address": shop.get("address", ""),
        "rating": "",
        "review_count": "",
        "url": get_nested(shop, "urls", "pc"),
        "hotpepper_id": shop.get("id", ""),
        "name_kana": shop.get("name_kana", ""),
        "station_name": shop.get("station_name", ""),
        "access": shop.get("access", ""),
        "lat": shop.get("lat", ""),
        "lng": shop.get("lng", ""),
        "catch": shop.get("catch", ""),
        "genre_catch": get_nested(shop, "genre", "catch"),
        "budget": get_nested(shop, "budget", "name"),
        "budget_average": shop.get("budget", {}).get("average", "") if isinstance(shop.get("budget"), dict) else "",
        "open": shop.get("open", ""),
        "close": shop.get("close", ""),
        "capacity": shop.get("capacity", ""),
        "parking": shop.get("parking", ""),
        "wifi": shop.get("wifi", ""),
        "card": shop.get("card", ""),
        "non_smoking": shop.get("non_smoking", ""),
        "middle_area_query": middle_area_query,
        "middle_area_code": get_nested(shop, "middle_area", "code"),
        "middle_area_name": get_nested(shop, "middle_area", "name"),
        "small_area_code": get_nested(shop, "small_area", "code"),
        "small_area_name": get_nested(shop, "small_area", "name"),
        "photo_url": get_nested(shop, "photo", "pc", "l"),
    }


def main() -> None:
    api_key = os.environ.get("HOTPEPPER_API_KEY")
    if not api_key:
        raise SystemExit("環境変数 HOTPEPPER_API_KEY が未設定です。")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for middle_area in MIDDLE_AREAS:
        start = 1
        while True:
            results = fetch_page(api_key, middle_area, start)
            available = int(results.get("results_available", 0))
            shops = results.get("shop", [])

            if isinstance(shops, dict):
                shops = [shops]
            if not shops:
                break

            for shop in shops:
                shop_id = str(shop.get("id", ""))
                if shop_id and shop_id in seen_ids:
                    continue
                if not is_cafe_like(shop):
                    continue
                rows.append(flatten_shop(shop, middle_area))
                if shop_id:
                    seen_ids.add(shop_id)

            returned = int(results.get("results_returned", len(shops)))
            next_start = start + returned
            if next_start > available:
                break

            start = next_start
            time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {OUT_CSV} rows={len(df)} cols={len(df.columns)}")


if __name__ == "__main__":
    main()
