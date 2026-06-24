from pathlib import Path
import pandas as pd
import folium


BASE_DIR = Path(__file__).resolve().parents[2]

PROPERTY_CSV_CANDIDATES = [
    BASE_DIR / "output" / "archive_csv" / "all_properties.csv",
    BASE_DIR / "output" / "all_properties.csv",
    BASE_DIR / "output" / "all_properties" / "all_properties.csv",
    BASE_DIR / "all_properties.csv",
]

PROPERTY_CSV = next(
    (p for p in PROPERTY_CSV_CANDIDATES if p.exists()),
    PROPERTY_CSV_CANDIDATES[0],
)

COMPETITOR_CSV = BASE_DIR / "data" / "competitors" / "competitors_geocoded.csv"
SUMMARY_CSV = BASE_DIR / "output" / "competitors" / "property_competitor_summary.csv"

OUT_PATH = BASE_DIR / "output" / "competitors" / "integrated_property_competitor_map.html"


def to_float(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def get_value(row, candidates):
    for col in candidates:
        if col in row and str(row.get(col, "")).strip():
            return row.get(col, "")
    return ""


def main():
    if not PROPERTY_CSV.exists():
        raise FileNotFoundError(f"物件CSVがありません: {PROPERTY_CSV}")

    if not COMPETITOR_CSV.exists():
        raise FileNotFoundError(f"競合CSVがありません: {COMPETITOR_CSV}")

    properties = pd.read_csv(PROPERTY_CSV, dtype=str).fillna("")
    competitors = pd.read_csv(COMPETITOR_CSV, dtype=str).fillna("")

    if SUMMARY_CSV.exists():
        summary = pd.read_csv(SUMMARY_CSV, dtype=str).fillna("")
    else:
        summary = pd.DataFrame()

    if not summary.empty and "property_index" in summary.columns:
        summary_map = {
            int(row["property_index"]): row
            for _, row in summary.iterrows()
            if str(row.get("property_index", "")).isdigit()
        }
    else:
        summary_map = {}

    property_points = []
    for i, row in properties.iterrows():
        lat = to_float(row.get("latitude"))
        lng = to_float(row.get("longitude"))
        if lat is not None and lng is not None:
            property_points.append((i, row, lat, lng))

    competitor_points = []
    for _, row in competitors.iterrows():
        lat = to_float(row.get("lat"))
        lng = to_float(row.get("lng"))
        if lat is not None and lng is not None:
            competitor_points.append((row, lat, lng))

    if not property_points:
        raise ValueError("緯度経度のある物件がありません。")

    center_lat = sum(lat for _, _, lat, _ in property_points) / len(property_points)
    center_lng = sum(lng for _, _, _, lng in property_points) / len(property_points)

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    property_layer = folium.FeatureGroup(name="物件", show=True)
    competitor_layer = folium.FeatureGroup(name="競合店舗", show=True)

    for i, row, lat, lng in property_points:
        name = get_value(row, ["物件名", "name", "property_name"])
        address = get_value(row, ["所在地", "address", "住所"])
        rent = get_value(row, ["賃料", "rent"])
        area = get_value(row, ["面積", "area"])
        score = get_value(row, ["総合スコア", "score", "評価点"])
        simulation_url = get_value(row, ["営業シミュレーションURL", "simulation_url"])

        s = summary_map.get(i)

        if s is not None:
            nearby_500 = s.get("nearby_500m_count", "0")
            nearby_1000 = s.get("nearby_1000m_count", "0")
            nearest_name = s.get("nearest_competitor_name", "")
            nearest_distance = s.get("nearest_competitor_distance_m", "")
        else:
            nearby_500 = "0"
            nearby_1000 = "0"
            nearest_name = ""
            nearest_distance = ""

        simulation_html = ""
        if simulation_url:
            simulation_html = f'<br><a href="{simulation_url}" target="_blank">営業シミュレーション</a>'

        html = f"""
        <div style="font-size:14px; line-height:1.6; width:280px;">
          <b>{name}</b><br>
          所在地：{address}<br>
          賃料：{rent}<br>
          面積：{area}<br>
          評価：{score}<br>
          <hr>
          <b>近隣競合</b><br>
          500m以内：{nearby_500}件<br>
          1km以内：{nearby_1000}件<br>
          最寄競合：{nearest_name}<br>
          距離：{nearest_distance}m
          {simulation_html}
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(html, max_width=340),
            tooltip=name,
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        ).add_to(property_layer)

    for row, lat, lng in competitor_points:
        name = row.get("store_name", "")
        genre = row.get("genre", "")
        address = row.get("address", "")
        rating = row.get("rating", "")
        review_count = row.get("review_count", "")
        url = row.get("url", "")

        url_html = ""
        if url:
            url_html = f'<br><a href="{url}" target="_blank">食べログページ</a>'

        html = f"""
        <div style="font-size:14px; line-height:1.6; width:260px;">
          <b>{name}</b><br>
          ジャンル：{genre}<br>
          住所：{address}<br>
          評価：{rating}<br>
          口コミ数：{review_count}
          {url_html}
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(html, max_width=320),
            tooltip=name,
            icon=folium.Icon(color="red", icon="coffee", prefix="fa"),
        ).add_to(competitor_layer)

    property_layer.add_to(m)
    competitor_layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m.save(OUT_PATH)

    print(f"[LOAD] properties: {PROPERTY_CSV} / {len(properties)} rows")
    print(f"[PLOT] properties: {len(property_points)}")
    print(f"[LOAD] competitors: {COMPETITOR_CSV} / {len(competitors)} rows")
    print(f"[PLOT] competitors: {len(competitor_points)}")
    print(f"[SAVE] {OUT_PATH}")


if __name__ == "__main__":
    main()