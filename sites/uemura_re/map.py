from pathlib import Path
import time

import folium
import pandas as pd
from geopy.geocoders import Nominatim

INPUT_CSV = Path(
    "output/uemura_re/uemura_re.csv"
)

GEOCODED_CSV = Path(
    "output/uemura_re/uemura_re_geocoded.csv"
)

FAILED_CSV = Path(
    "output/uemura_re/uemura_re_geocode_failed.csv"
)

MAP_HTML = Path(
    "output/uemura_re/uemura_re_map.html"
)


def normalize_address(addr):
    if pd.isna(addr):
        return None

    addr = str(addr).strip()

    addr = addr.replace("香川県", "")
    addr = addr.replace("--", "-")
    addr = addr.replace("－", "-")

    return addr


def main():
    df = pd.read_csv(INPUT_CSV)

    geolocator = Nominatim(
        user_agent="tenant_research_takamatsu"
    )

    lats = []
    lons = []

    failed_rows = []

    for idx, row in df.iterrows():

        address = row.get("所在地")

        address = normalize_address(address)

        lat = None
        lon = None

        if address:
            try:
                location = geolocator.geocode(
                    f"香川県高松市 {address}"
                )

                if location:
                    lat = location.latitude
                    lon = location.longitude

            except Exception as e:
                print(e)

            time.sleep(1)

        lats.append(lat)
        lons.append(lon)

        if lat is None:
            failed_rows.append(row.to_dict())

    df["latitude"] = lats
    df["longitude"] = lons

    df.to_csv(
        GEOCODED_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    pd.DataFrame(failed_rows).to_csv(
        FAILED_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    success_df = df.dropna(
        subset=["latitude", "longitude"]
    )

    if len(success_df):

        center_lat = success_df.iloc[0]["latitude"]
        center_lon = success_df.iloc[0]["longitude"]

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12
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