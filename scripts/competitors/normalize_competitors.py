from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

TABELOG_CSV = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"
HOTPEPPER_CSV = BASE_DIR / "data" / "competitors" / "raw" / "hotpepper_cafe_competitors.csv"
GOOGLE_MAPS_CSV = BASE_DIR / "output" / "google_maps" / "google_maps_geocoded.csv"

OUT_CSV = BASE_DIR / "data" / "competitors" / "competitors_master.csv"


def extract_memo_value(memo: str, key: str) -> str:
    if not isinstance(memo, str):
        return ""

    pattern = rf"{re.escape(key)}=([^|]*)"
    m = re.search(pattern, memo)
    if not m:
        return ""

    return m.group(1).strip()


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_tabelog() -> pd.DataFrame:
    df = pd.read_csv(TABELOG_CSV)

    rename_map = {
        "latitude": "lat",
        "longitude": "lng",
    }
    df = df.rename(columns=rename_map)

    for col in [
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
        "lat",
        "lng",
    ]:
        if col not in df.columns:
            df[col] = ""

    if (df["competitor_id"].fillna("") == "").all():
        df["competitor_id"] = [
            f"tabelog_{i + 1:04d}" for i in range(len(df))
        ]

    df["source"] = df["source"].fillna("tabelog").replace("", "tabelog")

    return df[
        [
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
            "lat",
            "lng",
        ]
    ]


def load_hotpepper() -> pd.DataFrame:
    df = pd.read_csv(HOTPEPPER_CSV)

    for col in [
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
    ]:
        if col not in df.columns:
            df[col] = ""

    df["lat"] = df["memo"].apply(lambda x: extract_memo_value(x, "lat"))
    df["lng"] = df["memo"].apply(lambda x: extract_memo_value(x, "lng"))

    df["source"] = "hotpepper"

    return df[
        [
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
            "lat",
            "lng",
        ]
    ]

def load_google_maps() -> pd.DataFrame:
    df = pd.read_csv(GOOGLE_MAPS_CSV)

    rename_map = {
        "name": "store_name",
        "latitude": "lat",
        "longitude": "lng",
        "map_url": "url",
        "google_maps_url": "url",
    }
    df = df.rename(columns=rename_map)

    for col in [
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
        "lat",
        "lng",
    ]:
        if col not in df.columns:
            df[col] = ""

    if (df["competitor_id"].fillna("") == "").all():
        df["competitor_id"] = [
            f"google_maps_{i + 1:04d}" for i in range(len(df))
        ]

    df["source"] = "google_maps"

    return df[
        [
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
            "lat",
            "lng",
        ]
    ]

def main() -> None:
    tabelog = load_tabelog()
    hotpepper = load_hotpepper()
    google_maps = load_google_maps()

    df = pd.concat([tabelog, hotpepper, google_maps], ignore_index=True)

    df["store_name_norm"] = df["store_name"].apply(normalize_text)
    df["address_norm"] = df["address"].apply(normalize_text)

    before = len(df)

    df = df.drop_duplicates(
        subset=["store_name_norm", "address_norm"],
        keep="first",
    )

    df = df.drop(columns=["store_name_norm", "address_norm"])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[LOAD] tabelog={len(tabelog)} hotpepper={len(hotpepper)} google_maps={len(google_maps)}")
    print(f"[DEDUP] before={before} after={len(df)} removed={before - len(df)}")
    print(f"[SAVE] {OUT_CSV}")


if __name__ == "__main__":
    main()