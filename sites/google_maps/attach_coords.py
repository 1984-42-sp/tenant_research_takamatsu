from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

HTML_PATH = BASE_DIR / "data" / "html" / "google_maps" / "search_result.html"
IN_PATH = BASE_DIR / "output" / "google_maps" / "google_maps_cafes.csv"
OUT_PATH = BASE_DIR / "output" / "google_maps" / "google_maps_geocoded.csv"

COORD_PATTERN = r"!3d([0-9]+\.[0-9]+)!4d([0-9]+\.[0-9]+)"


def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    df = pd.read_csv(IN_PATH)

    matches = re.findall(COORD_PATTERN, html)
    coords = list(dict.fromkeys(matches))

    print(f"[ROWS] csv rows: {len(df)}")
    print(f"[COORDS] unique coords: {len(coords)}")

    if len(coords) < len(df):
        print("[WARN] 座標数がCSV行数より少ないため、不足分は空欄になります")

    df["lat"] = ""
    df["lng"] = ""

    for i, (lat, lng) in enumerate(coords[: len(df)]):
        df.at[i, "lat"] = lat
        df.at[i, "lng"] = lng

    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {OUT_PATH}")

    print("\n=== preview ===")
    print(df[["competitor_id", "store_name", "address", "rating", "review_count", "lat", "lng"]].head(10))


if __name__ == "__main__":
    main()