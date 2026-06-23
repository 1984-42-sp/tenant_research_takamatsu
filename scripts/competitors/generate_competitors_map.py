from pathlib import Path
import pandas as pd
import folium


BASE_DIR = Path(__file__).resolve().parents[2]

IN_PATH = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"
OUT_PATH = BASE_DIR / "output" / "competitors" / "competitors_map.html"


def to_float(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def main():
    df = pd.read_csv(IN_PATH, dtype=str).fillna("")

    rows = []
    for _, row in df.iterrows():
        lat = to_float(row.get("lat"))
        lng = to_float(row.get("lng"))

        if lat is None or lng is None:
            continue

        rows.append((row, lat, lng))

    if not rows:
        raise ValueError("緯度経度のある競合店舗がありません。")

    center_lat = sum(lat for _, lat, _ in rows) / len(rows)
    center_lng = sum(lng for _, _, lng in rows) / len(rows)

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=14,
        tiles="OpenStreetMap",
    )

    for row, lat, lng in rows:
        name = row.get("store_name", "")
        genre = row.get("genre", "")
        address = row.get("address", "")
        rating = row.get("rating", "")
        review_count = row.get("review_count", "")
        source = row.get("source", "")
        url = row.get("url", "")

        html = f"""
        <div style="font-size:14px; line-height:1.6;">
          <b>{name}</b><br>
          ジャンル：{genre}<br>
          住所：{address}<br>
          評価：{rating}<br>
          口コミ数：{review_count}<br>
          情報源：{source}<br>
          <a href="{url}" target="_blank">URL</a>
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(html, max_width=300),
            tooltip=name,
            icon=folium.Icon(color="red", icon="coffee", prefix="fa"),
        ).add_to(m)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m.save(OUT_PATH)

    print(f"[LOAD] {IN_PATH}: {len(df)} rows")
    print(f"[PLOT] {len(rows)} rows")
    print(f"[SAVE] {OUT_PATH}")


if __name__ == "__main__":
    main()