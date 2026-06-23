from pathlib import Path
import math
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

PROPERTY_CSV_CANDIDATES = [
    BASE_DIR / "output" / "archive_csv" / "all_properties.csv",
    BASE_DIR / "output" / "all_properties.csv",
    BASE_DIR / "all_properties.csv",
]

PROPERTY_CSV = next(
    (path for path in PROPERTY_CSV_CANDIDATES if path.exists()),
    PROPERTY_CSV_CANDIDATES[0],
)
COMPETITOR_CSV = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"

OUT_DIR = BASE_DIR / "output" / "competitors"
NEARBY_OUT = OUT_DIR / "property_nearby_competitors.csv"
SUMMARY_OUT = OUT_DIR / "property_competitor_summary.csv"

RADIUS_LIST = [500, 1000]


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def to_float(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def main():
    if not PROPERTY_CSV.exists():
        raise FileNotFoundError(f"物件CSVがありません: {PROPERTY_CSV}")

    if not COMPETITOR_CSV.exists():
        raise FileNotFoundError(f"競合CSVがありません: {COMPETITOR_CSV}")

    properties = pd.read_csv(PROPERTY_CSV, dtype=str).fillna("")
    competitors = pd.read_csv(COMPETITOR_CSV, dtype=str).fillna("")

    property_rows = properties.copy()
    competitor_rows = competitors.copy()

    nearby_records = []

    for _, p in property_rows.iterrows():
        p_lat = to_float(p.get("latitude"))
        p_lng = to_float(p.get("longitude"))

        if p_lat is None or p_lng is None:
            continue

        property_name = p.get("物件名", "")
        property_address = p.get("所在地", "")
        property_url = p.get("営業シミュレーションURL", "")

        for _, c in competitor_rows.iterrows():
            c_lat = to_float(c.get("lat"))
            c_lng = to_float(c.get("lng"))

            if c_lat is None or c_lng is None:
                continue

            distance = haversine_m(p_lat, p_lng, c_lat, c_lng)

            if distance <= max(RADIUS_LIST):
                nearby_records.append(
                    {
                        "物件名": property_name,
                        "所在地": property_address,
                        "営業シミュレーションURL": property_url,
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

        for property_name, group in nearby_df.groupby("物件名"):
            group_sorted = group.sort_values("distance_m")
            first = group_sorted.iloc[0]

            summary_records.append(
                {
                    "物件名": property_name,
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

    print(f"[LOAD] properties: {len(properties)}")
    print(f"[LOAD] competitors: {len(competitors)}")
    print(f"[SAVE] {NEARBY_OUT}: {len(nearby_df)} rows")
    print(f"[SAVE] {SUMMARY_OUT}: {len(summary_df)} rows")


if __name__ == "__main__":
    main()