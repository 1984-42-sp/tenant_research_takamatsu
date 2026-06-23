from pathlib import Path
import re
import time
import unicodedata

from geopy import location
import pandas as pd
from geopy.geocoders import Nominatim, ArcGIS


BASE_DIR = Path(__file__).resolve().parents[2]

IN_PATH = BASE_DIR / "data" / "competitors" / "competitors_normalized.csv"
OUT_PATH = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"


def blank(v):
    return pd.isna(v) or str(v).strip() == ""


def clean_address(address):
    s = str(address).strip()
    s = unicodedata.normalize("NFKC", s)
    s = s.replace(" ", "")
    s = s.replace("香川県", "")
    s = s.replace("ー", "-").replace("－", "-").replace("―", "-")
    s = re.sub(r"-+", "-", s)

    # 階数・建物名・施設内表記を削る
    s = re.sub(r"(内|[0-9]+F|[0-9]+階|ビル.*|ビル[0-9A-Za-z]*|館.*|CUBE.*|alley.*|参番街.*)$", "", s)

    return s


def make_queries(store_name, address):
    cleaned = clean_address(address)

    queries = []

    if cleaned:
        queries.append(f"香川県{cleaned}")
        queries.append(f"{cleaned}, 香川県, 日本")

    if store_name:
        queries.append(f"{store_name} 高松市 香川県")
        queries.append(f"{store_name}, Takamatsu, Kagawa, Japan")

    return list(dict.fromkeys(queries))


def try_geocode(geocoder, query):
    try:
        return geocoder.geocode(query, timeout=10)
    except Exception:
        return None


def main():
    df = pd.read_csv(IN_PATH, dtype=str).fillna("")

    nominatim = Nominatim(
        user_agent="tenant_research_takamatsu_competitors",
        timeout=10,
    )
    arcgis = ArcGIS(timeout=10)

    success = 0
    failed = 0

    for i, row in df.iterrows():
        if not blank(row.get("lat")) and not blank(row.get("lng")):
            continue

        name = row.get("store_name", "")
        address = row.get("address", "")

        if blank(address):
            print(f"[SKIP] {name}: address blank")
            failed += 1
            continue

        queries = make_queries(name, address)

        location = None
        used_query = ""

        for query in queries:
            location = try_geocode(nominatim, query)
            used_query = query

            if location:
                break

            time.sleep(1)

            location = try_geocode(arcgis, query)
            used_query = query

            if location:
                break

            time.sleep(1)

        if location:
            df.at[i, "lat"] = str(location.latitude)
            df.at[i, "lng"] = str(location.longitude)
            print(f"[OK] {name}: {location.latitude}, {location.longitude} / {used_query}")
            success += 1
        else:
            print(f"[NG] {name}: {address}")
            failed += 1

        time.sleep(1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {OUT_PATH}")
    print(f"[RESULT] success={success}, failed={failed}, total={len(df)}")


if __name__ == "__main__":
    main()