from pathlib import Path
import math
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

PROPERTY_CSV_CANDIDATES = [
    BASE_DIR / "output" / "archive_csv" / "all_properties.csv",
    BASE_DIR / "output" / "all_properties.csv",
    BASE_DIR / "output" / "all_properties" / "all_properties.csv",
    BASE_DIR / "all_properties.csv",
]

PROPERTY_CSV = next(
    (p for p in PROPERTY_CSV_CANDIDATES if p.exists()),
    PROPERTY_CSV_CANDIDATES[0],
)

COMPETITOR_CSV = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"

OUT_DIR = BASE_DIR / "output" / "competitors"
NEARBY_OUT = OUT_DIR / "property_nearby_competitors.csv"
SUMMARY_OUT = OUT_DIR / "property_competitor_summary.csv"


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def to_float(v):
    try:
        if pd.isna(v) or str(v).strip() == "":
            return None
        return float(v)
    except ValueError:
        return None


def get_property_name(row):
    for col in ["物件名", "name", "property_name"]:
        if col in row and str(row.get(col, "")).strip():
            return row.get(col, "")
    return ""


def get_property_address(row):
    for col in ["所在地", "address", "住所"]:
        if col in row and str(row.get(col, "")).strip():
            return row.get(col, "")
    return ""


def main():
    if not PROPERTY_CSV.exists():
        raise FileNotFoundError(f"物件CSVがありません: {PROPERTY_CSV}")

    if not COMPETITOR_CSV.exists():
        raise FileNotFoundError(f"競合CSVがありません: {COMPETITOR_CSV}")

    properties = pd.read_csv(PROPERTY_CSV, dtype=str).fillna("")
    competitors = pd.read_csv(COMPETITOR_CSV, dtype=str).fillna("")

    nearby_records = []

    for p_index, p in properties.iterrows():
        p_lat = to_float(p.get("latitude"))
        p_lng = to_float(p.get("longitude"))

        if p_lat is None or p_lng is None:
            continue

        property_name = get_property_name(p)
        property_address = get_property_address(p)

        for _, c in competitors.iterrows():
            c_lat = to_float(c.get("lat"))
            c_lng = to_float(c.get("lng"))

            if c_lat is None or c_lng is None:
                continue

            distance = haversine_m(p_lat, p_lng, c_lat, c_lng)

            if distance <= 1000:
                nearby_records.append(
                    {
                        "property_index": p_index,
                        "物件名": property_name,
                        "所在地": property_address,
                        "property_latitude": p_lat,
                        "property_longitude": p_lng,
                        "competitor_id": c.get("competitor_id", ""),
                        "competitor_name": c.get("store_name", ""),
                        "competitor_genre": c.get("genre", ""),
                        "competitor_source": c.get("source", ""),
                        "competitor_address": c.get("address", ""),
                        "competitor_lat": c_lat,
                        "competitor_lng": c_lng,
                        "rating": c.get("rating", ""),
                        "review_count": c.get("review_count", ""),
                        "url": c.get("url", ""),
                        "distance_m": round(distance, 1),
                        "within_500m": distance <= 500,
                        "within_1000m": distance <= 1000,
                    }
                )

    nearby_df = pd.DataFrame(nearby_records)

    if nearby_df.empty:
        summary_df = pd.DataFrame(
            columns=[
                "property_index",
                "物件名",
                "所在地",
                "nearby_500m_count",
                "nearby_1000m_count",
                "nearest_competitor_name",
                "nearest_competitor_distance_m",
            ]
        )
    else:
        summary_records = []

        for property_index, group in nearby_df.groupby("property_index"):
            group_sorted = group.sort_values("distance_m")
            first = group_sorted.iloc[0]

            summary_records.append(
                {
                    "property_index": property_index,
                    "物件名": first.get("物件名", ""),
                    "所在地": first.get("所在地", ""),
                    "nearby_500m_count": int(group["within_500m"].sum()),
                    "nearby_1000m_count": int(group["within_1000m"].sum()),
                    "nearest_competitor_name": first.get("competitor_name", ""),
                    "nearest_competitor_distance_m": first.get("distance_m", ""),
                }
            )

        summary_df = pd.DataFrame(summary_records)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    nearby_df.to_csv(NEARBY_OUT, index=False, encoding="utf-8-sig")
    summary_df.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")

    print(f"[LOAD] properties: {PROPERTY_CSV} / {len(properties)} rows")
    print(f"[LOAD] competitors: {COMPETITOR_CSV} / {len(competitors)} rows")
    print(f"[SAVE] {NEARBY_OUT}: {len(nearby_df)} rows")
    print(f"[SAVE] {SUMMARY_OUT}: {len(summary_df)} rows")


if __name__ == "__main__":
    main()