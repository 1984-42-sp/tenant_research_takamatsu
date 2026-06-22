from pathlib import Path
import importlib.util
import time

import folium
import pandas as pd
from geopy.geocoders import Nominatim


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = Path(__file__).resolve().parent

selectors_path = SITE_DIR / "selectors.py"
spec = importlib.util.spec_from_file_location(
    "setouchi_bluesky_selectors",
    selectors_path,
)
selectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selectors)

OUTPUT_DIR = ROOT / "output" / selectors.SITE_NAME
INPUT_CSV = OUTPUT_DIR / selectors.OUTPUT_MERGED_CSV
GEOCODED_CSV = OUTPUT_DIR / selectors.OUTPUT_GEOCODED_CSV
GEOCODE_FAILED_CSV = OUTPUT_DIR / selectors.OUTPUT_GEOCODE_FAILED_CSV
MAP_HTML = OUTPUT_DIR / selectors.OUTPUT_MAP_HTML


def clean_address(address):
    if pd.isna(address):
        return ""

    text = str(address).strip()
    text = text.replace("－", "-")
    text = text.replace("--", "-")
    return text


def main():
    df = pd.read_csv(INPUT_CSV)
    geolocator = Nominatim(user_agent="tenant_research_takamatsu")

    latitudes = []
    longitudes = []

    for _, row in df.iterrows():
        address = clean_address(row.get("所在地", ""))

        if not address:
            latitudes.append(None)
            longitudes.append(None)
            continue

        location = geolocator.geocode(address, country_codes="jp", timeout=10)

        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
            print(f"OK: {address} -> {location.latitude}, {location.longitude}")
        else:
            latitudes.append(None)
            longitudes.append(None)
            print(f"NG: {address}")

        time.sleep(1)

    df["latitude"] = latitudes
    df["longitude"] = longitudes

    geocoded_df = df.dropna(subset=["latitude", "longitude"]).copy()
    failed_df = df[df["latitude"].isna() | df["longitude"].isna()].copy()

    geocoded_df.to_csv(GEOCODED_CSV, index=False, encoding="utf-8-sig")
    failed_df.to_csv(GEOCODE_FAILED_CSV, index=False, encoding="utf-8-sig")

    print(f"geocoded: {len(geocoded_df)}")
    print(f"failed: {len(failed_df)}")

    m = folium.Map(location=[34.3428, 134.0466], zoom_start=13)

    for _, row in geocoded_df.iterrows():
        title = row.get("title", "")
        address = row.get("所在地", "")
        rent = row.get("賃料", "")
        area = row.get("使用部分面積", "")
        food = row.get("飲食店可否", "")
        url = row.get("detail_url_list", row.get("detail_url", ""))

        popup_html = f"""
        <b>{title}</b><br>
        所在地: {address}<br>
        賃料: {rent}<br>
        面積: {area}<br>
        飲食店可否: {food}<br>
        <a href="{url}" target="_blank">詳細ページ</a>
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=400),
            tooltip=title,
        ).add_to(m)

    m.save(MAP_HTML)

    print(f"saved geocoded: {GEOCODED_CSV}")
    print(f"saved failed: {GEOCODE_FAILED_CSV}")
    print(f"saved map: {MAP_HTML}")


if __name__ == "__main__":
    main()