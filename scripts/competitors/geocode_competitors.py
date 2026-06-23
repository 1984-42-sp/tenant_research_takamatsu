from pathlib import Path
import time
import pandas as pd
from geopy.geocoders import Nominatim

BASE_DIR = Path(__file__).resolve().parents[2]
IN_PATH = BASE_DIR / "data" / "competitors" / "competitors_normalized.csv"
OUT_PATH = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"

def blank(v):
    return pd.isna(v) or str(v).strip() == ""

def main():
    df = pd.read_csv(IN_PATH, dtype=str).fillna("")
    geolocator = Nominatim(user_agent="tenant_research_takamatsu_competitors", timeout=10)

    success = 0
    failed = 0

    for i, row in df.iterrows():
        if not blank(row.get("lat")) and not blank(row.get("lng")):
            continue

        name = row.get("store_name", "")
        addr = row.get("address", "")

        if blank(addr):
            print(f"[SKIP] {name}: address blank")
            failed += 1
            continue

        query = f"香川県{addr}"

        try:
            loc = geolocator.geocode(query)
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            failed += 1
            time.sleep(1)
            continue

        if loc:
            df.at[i, "lat"] = loc.latitude
            df.at[i, "lng"] = loc.longitude
            print(f"[OK] {name}: {loc.latitude}, {loc.longitude}")
            success += 1
        else:
            print(f"[NG] {name}: {query}")
            failed += 1

        time.sleep(1)

    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {OUT_PATH}")
    print(f"[RESULT] success={success}, failed={failed}, total={len(df)}")

if __name__ == "__main__":
    main()