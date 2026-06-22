import time

import pandas as pd
from geopy.geocoders import Nominatim

df = pd.read_csv(
    "output/tenant_kagawa/tenant_kagawa.csv"
)

geolocator = Nominatim(
    user_agent="tenant_research_takamatsu"
)

latitudes = []
longitudes = []

for i, address in enumerate(df["address"], start=1):

    address = str(address)

    address = address.replace("--", "-")
    address = address.replace("－", "-")

    if not address.startswith("香川県"):
        address = "香川県" + address
    
    print(
        f"{i}/{len(df)} {address}"
    )

    try:

        location = geolocator.geocode(
            address
        )

        if location:

            latitudes.append(
                location.latitude
            )

            longitudes.append(
                location.longitude
            )

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
    "output/tenant_kagawa/tenant_kagawa_geocoded.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print(df.shape)

print()
print(
    df["latitude"].notna().sum()
)

print()

failed = df[
    df["latitude"].isna()
][["article_id", "address"]]

print(failed)

import folium

valid_df = df.dropna(
    subset=["latitude", "longitude"]
)

center_lat = valid_df[
    "latitude"
].mean()

center_lon = valid_df[
    "longitude"
].mean()

m = folium.Map(
    location=[
        center_lat,
        center_lon
    ],
    zoom_start=12
)

for _, row in valid_df.iterrows():

    popup = (
        f"{row['name']}<br>"
        f"{row['address']}<br>"
        f"{row['rent_fee']}"
    )

    folium.Marker(
        [
            row["latitude"],
            row["longitude"]
        ],
        popup=popup
    ).add_to(m)

m.save(
    "output/tenant_kagawa/tenant_kagawa_map.html"
)

print()
print(
    "map saved"
)

failed = df[
    df["latitude"].isna()
]

failed.to_csv(
    "output/tenant_kagawa/tenant_kagawa_geocode_failed.csv",
    index=False,
    encoding="utf-8-sig"
)

print(
    "failed:",
    len(failed)
)