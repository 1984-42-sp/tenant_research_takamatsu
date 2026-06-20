from pathlib import Path
import time

import folium
import pandas as pd
from geopy.geocoders import Nominatim

INPUT_CSV = Path("output/tenant_shop/tenant_shop.csv")

GEOCODED_CSV = Path("output/tenant_shop/tenant_shop_geocoded.csv")
FAILED_CSV = Path("output/tenant_shop/tenant_shop_geocode_failed.csv")
MAP_HTML = Path("output/tenant_shop_map.html")


def normalize_address(addr):
    if pd.isna(addr):
        return None

    addr = str(addr).strip()
    addr = addr.replace("香川県", "")
    addr = addr.replace("高松市高松市", "高松市")
    addr = addr.replace("--", "-")
    addr = addr.replace("－", "-")

    return addr


def build_queries(address):
    if not address:
        return []

    queries = []

    if address.startswith("高松市"):
        queries.append(f"香川県{address}")
        queries.append(address)
    else:
        queries.append(f"香川県高松市{address}")
        queries.append(f"高松市{address}")

    # 番地で失敗した場合の町名 fallback
    if "百間町" in address:
        queries.append("香川県高松市百間町")
        queries.append("高松市百間町")

    return queries


def main():
    df = pd.read_csv(INPUT_CSV)

    geolocator = Nominatim(
        user_agent="tenant_research_takamatsu"
    )

    lats = []
    lons = []
    geocode_queries = []
    geocode_levels = []

    failed_rows = []

    for _, row in df.iterrows():
        address = normalize_address(row.get("所在地"))

        lat = None
        lon = None
        used_query = None
        level = None

        for query in build_queries(address):
            print(f"[geocode] {query}")

            try:
                location = geolocator.geocode(query)

                if location:
                    lat = location.latitude
                    lon = location.longitude
                    used_query = query
                    level = "町名fallback" if query.endswith("百間町") else "住所"
                    print(f"[hit] {lat}, {lon}")
                    break

            except Exception as e:
                print(e)

            time.sleep(1)

        lats.append(lat)
        lons.append(lon)
        geocode_queries.append(used_query)
        geocode_levels.append(level)

        if lat is None:
            failed_rows.append(row.to_dict())

    df["latitude"] = lats
    df["longitude"] = lons
    df["geocode_query"] = geocode_queries
    df["geocode_level"] = geocode_levels

    df.to_csv(GEOCODED_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(failed_rows).to_csv(FAILED_CSV, index=False, encoding="utf-8-sig")

    success_df = df.dropna(subset=["latitude", "longitude"])

    if len(success_df):
        m = folium.Map(
            location=[
                success_df.iloc[0]["latitude"],
                success_df.iloc[0]["longitude"],
            ],
            zoom_start=16,
        )

        for _, row in success_df.iterrows():
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=row.get("物件名", ""),
            ).add_to(m)

        m.save(MAP_HTML)

    print(f"total   : {len(df)}")
    print(f"success : {len(success_df)}")
    print(f"failed  : {len(failed_rows)}")
    print(f"saved   : {GEOCODED_CSV}")
    print(f"saved   : {FAILED_CSV}")
    print(f"saved   : {MAP_HTML}")


if __name__ == "__main__":
    main()