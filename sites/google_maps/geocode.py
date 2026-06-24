from pathlib import Path
import time
import pandas as pd
from geopy.geocoders import Nominatim

BASE_DIR = Path(__file__).resolve().parents[2]

IN_PATH = BASE_DIR / "output" / "google_maps" / "google_maps_cafes.csv"
OUT_PATH = BASE_DIR / "output" / "google_maps" / "google_maps_geocoded.csv"

ADDRESS_COL = "address"
LAT_COL = "lat"
LNG_COL = "lng"


def geocode_address(geolocator, address: str):
    if not isinstance(address, str) or not address.strip():
        return None, None

    query = address.strip()

    try:
        location = geolocator.geocode(
            query,
            country_codes="jp",
            timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] {query}: {e}")
        return None, None

    if location is None:
        return None, None

    return location.latitude, location.longitude


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"入力CSVが見つかりません: {IN_PATH}")

    df = pd.read_csv(IN_PATH)

    if ADDRESS_COL not in df.columns:
        raise ValueError(f"{ADDRESS_COL} 列がありません")

    if LAT_COL not in df.columns:
        df[LAT_COL] = ""

    if LNG_COL not in df.columns:
        df[LNG_COL] = ""

    geolocator = Nominatim(user_agent="tenant_research_takamatsu_google_maps")

    success = 0
    failed = 0

    for idx, row in df.iterrows():
        address = row.get(ADDRESS_COL, "")

        existing_lat = row.get(LAT_COL, "")
        existing_lng = row.get(LNG_COL, "")

        if pd.notna(existing_lat) and pd.notna(existing_lng) and str(existing_lat).strip() and str(existing_lng).strip():
            continue

        lat, lng = geocode_address(geolocator, address)

        if lat is not None and lng is not None:
            df.at[idx, LAT_COL] = lat
            df.at[idx, LNG_COL] = lng
            success += 1
            print(f"[OK] {address} -> {lat}, {lng}")
        else:
            failed += 1
            print(f"[NG] {address}")

        time.sleep(1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"\n[SAVE] {OUT_PATH}")
    print(f"[SUCCESS] {success}")
    print(f"[FAILED] {failed}")


if __name__ == "__main__":
    main()
    