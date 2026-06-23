from pathlib import Path
import re
import pandas as pd
import folium


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"

SOURCES = [
    ("テナント香川", "tenant_kagawa"),
    ("高松ハウジングサービス", "takamatsu_housing"),
    ("瀬戸内ブルースカイ", "setouchi_bluesky"),
    ("植村不動産", "uemura_re"),
    ("エムクレア", "mcrea"),
    ("テナントショップ", "tenant_shop"),
]


COMMON_COLUMNS = [
    "物件名",
    "所在地",
    "家賃",
    "面積",
    "坪数",
    "飲食可否",
    "掲載サイト",
    "詳細URL",
    "住所取得可否",
    "latitude",
    "longitude",
    "家賃数値",
    "面積数値",
    "坪数数値",
]


def first_existing(row, candidates):
    for col in candidates:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    return ""


def extract_number(value):
    if pd.isna(value):
        return None
    text = str(value).replace(",", "")
    m = re.search(r"[\d.]+", text)
    return float(m.group()) if m else None


def judge_food_allowed(row):
    direct_cols = [
        "飲食店可否",
        "飲食可否",
        "飲食",
        "飲食店",
    ]

    for col in direct_cols:
        if col in row and pd.notna(row[col]):
            value = str(row[col]).strip()

            if value in ["可", "飲食可", "飲食店可", "軽飲食可", "重飲食可"]:
                return "可"

            if value in ["不可", "飲食不可", "飲食店不可", "飲食NG", "重飲食不可"]:
                return "不可"

    text = " ".join(str(v) for v in row.values if pd.notna(v))

    ng_words = [
        "飲食不可",
        "飲食店不可",
        "飲食NG",
        "重飲食不可",
    ]

    ok_words = [
        "飲食店可",
        "飲食可",
        "軽飲食可",
        "重飲食可",
        "飲食相談",
        "飲食可能",
    ]

    if any(w in text for w in ng_words):
        return "不可"

    if any(w in text for w in ok_words):
        return "可"

    return "確認必要"


def normalize_one(site_name, path):
    if not path.exists():
        print(f"[WARN] missing: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path, dtype=str).fillna("")
    print(f"[LOAD] {site_name}: {len(df)}件")

    rows = []

    for _, row in df.iterrows():
        item = {}

        item["物件名"] = first_existing(row, [
            "物件名", "name", "title", "建物名"
        ])

        item["所在地"] = first_existing(row, [
            "所在地", "住所", "address", "所在地住所"
        ])

        item["家賃"] = first_existing(row, [
            "家賃", "賃料", "rent", "price"
        ])

        item["面積"] = first_existing(row, [
            "面積",
            "契約面積",
            "専有面積",
            "使用部分面積",
            "建物面積",
            "土地面積",
            "area",
        ])

        item["坪数"] = first_existing(row, [
            "坪数",
            "坪",
            "坪数/坪単価",
            "坪単価",
            "tsubo",
        ])

        item["詳細URL"] = first_existing(row, [
            "詳細URL",
            "詳細ページURL",
            "detail_url",
            "detail_url_detail",
            "detail_url_list",
            "url",
        ])

        item["掲載サイト"] = site_name
        item["飲食可否"] = judge_food_allowed(row)

        item["latitude"] = first_existing(row, [
            "latitude", "lat", "緯度"
        ])

        item["longitude"] = first_existing(row, [
            "longitude", "lon", "lng", "経度"
        ])

        item["住所取得可否"] = (
            "取得済み"
            if item["latitude"] and item["longitude"]
            else "未取得"
        )

        item["家賃数値"] = extract_number(item["家賃"])
        item["面積数値"] = extract_number(item["面積"])
        item["坪数数値"] = extract_number(item["坪数"])

        rows.append(item)

    return pd.DataFrame(rows)


def save_map(df):
    map_df = df[
        (df["latitude"].astype(str).str.len() > 0) &
        (df["longitude"].astype(str).str.len() > 0)
    ].copy()

    map_df["latitude"] = pd.to_numeric(map_df["latitude"], errors="coerce")
    map_df["longitude"] = pd.to_numeric(map_df["longitude"], errors="coerce")
    map_df = map_df.dropna(subset=["latitude", "longitude"])

    m = folium.Map(location=[34.3428, 134.0466], zoom_start=13)

    for _, row in map_df.iterrows():
        color = "green" if row["飲食可否"] == "可" else "blue"

        popup_html = f"""
        <b>{row['物件名']}</b><br>
        所在地：{row['所在地']}<br>
        家賃：{row['家賃']}<br>
        面積：{row['面積']}<br>
        掲載サイト：{row['掲載サイト']}<br>
        <a href="{row['詳細URL']}" target="_blank">詳細ページ</a>
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=350),
            icon=folium.Icon(color=color),
        ).add_to(m)

    out = (
    OUTPUT_DIR
    / "all_properties"
    / "all_properties_map.html"
    )
    m.save(out)
    print(f"[SAVE] {out}")


def save_list_html(df):
    display_cols = [
        "物件名",
        "所在地",
        "家賃",
        "面積",
        "坪数",
        "飲食可否",
        "住所取得可否",
        "掲載サイト",
        "詳細URL",
        "家賃数値",
        "坪数数値",
        "面積数値",
    ]

    html_table = df[display_cols].to_html(
        index=False,
        escape=False,
        table_id="properties",
        classes="display nowrap",
    )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>高松市 事業用賃貸物件一覧</title>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
<style>
body {{
  font-family: sans-serif;
  margin: 20px;
}}
table {{
  width: 100%;
}}
a {{
  color: #0066cc;
}}
</style>
</head>
<body>
<h1>高松市 事業用賃貸物件一覧</h1>
<p>住所取得失敗物件も含む統合一覧です。地図には住所取得済み物件のみ表示しています。</p>

{html_table}

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready(function() {{
  $('#properties').DataTable({{
    pageLength: 25,
    order: [],
    columnDefs: [
      {{
        targets: 8,
        render: function(data, type, row) {{
          if (!data) return "";
          return '<a href="' + data + '" target="_blank">詳細</a>';
        }}
      }},
      {{
        targets: [9, 10, 11],
        visible: false
      }}
    ],
    initComplete: function () {{
      this.api().columns([5, 6, 7]).every(function () {{
        var column = this;
        var select = $('<select><option value="">すべて</option></select>')
          .appendTo($(column.header()))
          .on('change', function () {{
            var val = $.fn.dataTable.util.escapeRegex($(this).val());
            column.search(val ? '^' + val + '$' : '', true, false).draw();
          }});
        column.data().unique().sort().each(function (d) {{
          if (d) select.append('<option value="' + d + '">' + d + '</option>');
        }});
      }});
    }}
  }});
}});
</script>
</body>
</html>
"""

    out = (
    OUTPUT_DIR
    / "all_properties"
    / "all_properties_list.html"
    )
    out.write_text(html, encoding="utf-8")
    print(f"[SAVE] {out}")


def main():
    frames = []

    for site_name, site_dir in SOURCES:
        base_csv = OUTPUT_DIR / site_dir / f"{site_dir}.csv"
        geocoded_csv = OUTPUT_DIR / site_dir / f"{site_dir}_geocoded.csv"

        base_df = normalize_one(site_name, base_csv)

        if base_df.empty:
            continue

        if geocoded_csv.exists():
            geo_df = normalize_one(site_name, geocoded_csv)

            if not geo_df.empty:
                geo_keys = geo_df[[
                    "物件名",
                    "所在地",
                    "掲載サイト",
                    "latitude",
                    "longitude",
                ]].copy()

                geo_keys = geo_keys.drop_duplicates(
                    subset=["物件名", "所在地", "掲載サイト"],
                    keep="first"
                )

                base_df = base_df.merge(
                    geo_keys,
                    on=["物件名", "所在地", "掲載サイト"],
                    how="left",
                    suffixes=("", "_geo")
                )

                base_df["latitude"] = base_df["latitude_geo"].fillna(base_df["latitude"])
                base_df["longitude"] = base_df["longitude_geo"].fillna(base_df["longitude"])

                base_df = base_df.drop(columns=["latitude_geo", "longitude_geo"])

        base_df["住所取得可否"] = base_df.apply(
            lambda r: "取得済み"
            if str(r["latitude"]).strip() and str(r["longitude"]).strip()
            else "未取得",
            axis=1
        )

        frames.append(base_df)

    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df[COMMON_COLUMNS]

    before = len(all_df)

    all_df = all_df.drop_duplicates(
        subset=["物件名", "所在地", "家賃", "掲載サイト"],
        keep="first"
    )

    after = len(all_df)

    print(f"[INFO] loaded total: {before}件")
    print(f"[INFO] duplicated removed: {before - after}件")
    print(f"[INFO] final total: {after}件")

    all_properties_dir = OUTPUT_DIR / "all_properties"
    all_properties_dir.mkdir(parents=True, exist_ok=True)

    all_csv = all_properties_dir / "all_properties.csv"
    all_df.to_csv(all_csv, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {all_csv}")

    geocoded = all_df[all_df["住所取得可否"] == "取得済み"].copy()
    failed = all_df[all_df["住所取得可否"] == "未取得"].copy()

    geocoded_csv = all_properties_dir / "all_properties_geocoded.csv"
    failed_csv = all_properties_dir / "all_properties_geocode_failed.csv"

    geocoded.to_csv(geocoded_csv, index=False, encoding="utf-8-sig")
    failed.to_csv(failed_csv, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {geocoded_csv}: {len(geocoded)}件")
    print(f"[SAVE] {failed_csv}: {len(failed)}件")

    # 旧マップ生成は停止。
    # マップは scripts/generate_enhanced_property_map.py で生成する。
    # save_map(all_df)

    save_list_html(all_df)


if __name__ == "__main__":
    main()