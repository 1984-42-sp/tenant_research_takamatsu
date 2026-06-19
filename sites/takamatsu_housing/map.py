import time

import folium
import pandas as pd
from geopy.geocoders import Nominatim

INPUT_PATH = "output/takamatsu_housing.csv"
GEOCODED_PATH = "output/takamatsu_housing_geocoded.csv"
FAILED_PATH = "output/takamatsu_housing_geocode_failed.csv"
MAP_PATH = "output/takamatsu_housing_map.html"

df = pd.read_csv(INPUT_PATH)

geolocator = Nominatim(
    user_agent="tenant_research_takamatsu"
)

latitudes = []
longitudes = []

for i, address in enumerate(df["所在地"], start=1):

    address = str(address)

    print(f"{i}/{len(df)} {address}")

    try:
        location = geolocator.geocode(address)

        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
        else:
            latitudes.append(None)
            longitudes.append(None)

    except Exception as e:
        print(e)
        latitudes.append(None)
        longitudes.append(None)

    time.sleep(1)

df["latitude"] = latitudes
df["longitude"] = longitudes

df.to_csv(
    GEOCODED_PATH,
    index=False,
    encoding="utf-8-sig"
)

failed = df[
    df["latitude"].isna()
]

failed.to_csv(
    FAILED_PATH,
    index=False,
    encoding="utf-8-sig"
)

valid_df = df.dropna(
    subset=["latitude", "longitude"]
)

print()
print("total:", len(df))
print("geocode success:", len(valid_df))
print("geocode failed:", len(failed))

m = folium.Map(
    location=[
        valid_df["latitude"].mean(),
        valid_df["longitude"].mean(),
    ],
    zoom_start=12
)

for _, row in valid_df.iterrows():

    popup = (
        f"{row['name']}<br>"
        f"{row['所在地']}<br>"
        f"{row['賃料']}<br>"
        f"{row['飲食店可否']}"
    )

    folium.Marker(
        [
            row["latitude"],
            row["longitude"]
        ],
        popup=popup
    ).add_to(m)

m.save(MAP_PATH)

print()
print(f"saved: {GEOCODED_PATH}")
print(f"saved: {FAILED_PATH}")
print(f"saved: {MAP_PATH}")