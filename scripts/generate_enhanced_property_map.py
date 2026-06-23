from pathlib import Path
import json
import html

import folium
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_DASHBOARD = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"
INPUT_BUSINESS_PLAN = BASE_DIR / "output" / "all_properties" / "business_plan_dashboard.csv"
INPUT_SIM_INDEX = BASE_DIR / "output" / "archive_csv" / "property_business_simulations_index.csv"

OUTPUT_HTML = BASE_DIR / "output" / "all_properties" / "all_properties_map.html"
OUTPUT_FINAL_HTML = BASE_DIR / "output" / "final_html" / "all_properties_map.html"


PATTERN_COLORS = {
    "低固定費・小商圏型": "#2f80ed",
    "中心街・高単価型": "#f2994a",
    "中心街・高回転型": "#eb5757",
    "準中心街・生活圏型": "#9b51e0",
    "郊外・駐車場依存型": "#27ae60",
    "大型投資・高売上必須型": "#8e44ad",
    "家賃未定・問い合わせ必要型": "#828282",
    "要確認・情報不足型": "#828282",
    "面積不明・詳細確認型": "#8c564b",
    "飲食不可・評価対象外型": "#000000",
}


def esc(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def clean_value(value):
    if pd.isna(value):
        return ""
    return value


def load_simulation_link_map():
    if not INPUT_SIM_INDEX.exists():
        print(f"[WARN] simulation index not found: {INPUT_SIM_INDEX}")
        return {}

    sim_df = pd.read_csv(INPUT_SIM_INDEX)

    name_col = "物件名"

    file_col = None
    for col in sim_df.columns:
        if col in ["営業シミュレーションURL", "ファイル名", "html_file", "simulation_file", "filename", "file_name"]:
            file_col = col
            break

    if file_col is None:
        for col in sim_df.columns:
            if "html" in col.lower() or "file" in col.lower() or "ファイル" in col:
                file_col = col
                break

    if name_col not in sim_df.columns or file_col is None:
        print("[WARN] simulation index columns not matched")
        print(sim_df.columns.tolist())
        return {}

    result = {}

    for _, row in sim_df.iterrows():
        name = str(row.get(name_col, "")).strip()
        filename = str(row.get(file_col, "")).strip()

        if not name or not filename:
            continue

        if not filename.startswith("property_business_simulations/"):
            filename = f"property_business_simulations/{filename}"

        result[name] = filename

    return result


def load_data():
    df = pd.read_csv(INPUT_DASHBOARD)

    if INPUT_BUSINESS_PLAN.exists():
        bp = pd.read_csv(INPUT_BUSINESS_PLAN)

        bp_cols = [
            col for col in [
                "物件名",
                "seongsu_fit_stars",
                "seongsu_fit_score",
                "seongsu_fit_type",
                "seongsu_fit_comment",
                "seongsu_rank",
            ]
            if col in bp.columns
        ]

        if "物件名" in bp_cols:
            bp = bp[bp_cols].drop_duplicates(subset=["物件名"], keep="first")
            df = df.merge(bp, on="物件名", how="left")

    sim_map = load_simulation_link_map()
    df["営業シミュレーションURL"] = df["物件名"].map(sim_map).fillna("")

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    return df


def make_points(df):
    points = []

    for _, row in df.iterrows():
        pattern = str(row.get("事業成立パターン", ""))
        color = PATTERN_COLORS.get(pattern, "#2d9cdb")

        points.append({
            "物件名": clean_value(row.get("物件名")),
            "所在地": clean_value(row.get("所在地")),
            "掲載サイト": clean_value(row.get("掲載サイト")),
            "詳細URL": clean_value(row.get("詳細URL")),
            "営業シミュレーションURL": clean_value(row.get("営業シミュレーションURL")),
            "latitude": float(row.get("latitude")),
            "longitude": float(row.get("longitude")),
            "家賃": clean_value(row.get("家賃")),
            "坪数": clean_value(row.get("坪数_補正")),
            "飲食可否": clean_value(row.get("飲食可否")),
            "立地区分": clean_value(row.get("立地区分")),
            "事業成立パターン": pattern,
            "推奨カフェモデル": clean_value(row.get("推奨カフェモデル")),
            "必要月商": clean_value(row.get("必要月商")),
            "推奨必要日客数": clean_value(row.get("推奨必要日客数")),
            "初期投資中央値": clean_value(row.get("初期投資中央値")),
            "評価ランク": clean_value(row.get("評価ランク")),
            "評価コメント": clean_value(row.get("評価コメント")),
            "seongsu_fit_stars": clean_value(row.get("seongsu_fit_stars")),
            "seongsu_fit_score": clean_value(row.get("seongsu_fit_score")),
            "seongsu_fit_type": clean_value(row.get("seongsu_fit_type")),
            "seongsu_fit_comment": clean_value(row.get("seongsu_fit_comment")),
            "color": color,
        })

    return points


def main():
    df = load_data()
    points = make_points(df)

    m = folium.Map(
        location=[34.3428, 134.0466],
        zoom_start=13,
        tiles="CartoDB Voyager",
        control_scale=True,
    )

    map_name = m.get_name()
    points_json = json.dumps(points, ensure_ascii=False)

    custom_html = """
<div class="topbar">
  <div>
    <div class="brand">☕ Takamatsu Cafe Project</div>
    <div class="subtitle">高松市 カフェ開業候補地マップ</div>
  </div>
  <div class="top-stats">
    <div class="stat"><span>表示物件</span><strong id="totalCount">-</strong></div>
    <div class="stat"><span>地図表示</span><strong id="mapCount">-</strong></div>
  </div>
</div>

<div class="legend-card">
  <div class="legend-title">事業成立パターン</div>
  <div id="legendItems"></div>
</div>

<div class="side-panel" id="sidePanel">
  <div class="panel-empty">
    <h2>物件を選択してください</h2>
    <p>地図上のピンをクリックすると、ここに事業性評価・営業シミュレーション・ソンス評価が表示されます。</p>
  </div>
</div>
"""

    custom_css = """
<style>
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.leaflet-container {
  background: #f7f2ea;
}

.topbar {
  position: fixed;
  z-index: 9999;
  top: 18px;
  left: 18px;
  right: 420px;
  height: 64px;
  background: rgba(38, 29, 22, 0.92);
  color: white;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.22);
  backdrop-filter: blur(10px);
}

.brand {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.subtitle {
  font-size: 10px;
  color: #fff1d8;
  margin-top: 4px;
}

.top-stats {
  display: flex;
  gap: 8px;
}

.stat {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  padding: 4px 10px;
  min-width: 70px;
  text-align: center;
}

.stat span {
  display: block;
  font-size: 9px;
  color: #e6d8c5;
}

.stat strong {
  font-size: 14px;
  color: #ffd36a;
}

.legend-card {
  position: fixed;
  z-index: 9999;
  left: 22px;
  bottom: 28px;
  width: 260px;
  background: rgba(255,255,255,0.94);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.14);
  backdrop-filter: blur(8px);
}

.legend-title {
  font-weight: 800;
  margin-bottom: 12px;
  color: #2d241c;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  margin: 9px 0;
  color: #2f261f;
  font-weight: 700;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.06);
}

.side-panel {
  position: fixed;
  z-index: 9999;
  top: 18px;
  right: 18px;
  bottom: 18px;
  width: 370px;
  background: rgba(255,255,255,0.96);
  border-radius: 22px;
  box-shadow: 0 16px 42px rgba(0,0,0,0.18);
  overflow-y: auto;
  backdrop-filter: blur(12px);
}

.panel-empty {
  padding: 28px;
  color: #4a4037;
  line-height: 1.8;
}

.close-panel-btn{
    position:absolute;
    top:12px;
    right:12px;

    width:34px;
    height:34px;

    border:none;
    border-radius:50%;

    background:rgba(255,255,255,0.25);
    color:white;

    cursor:pointer;
    font-size:18px;
    font-weight:700;

    transition:.2s;
}

.close-panel-btn:hover{
    background:rgba(255,255,255,0.45);
}

.panel-content {
  padding: 24px;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 18px;
}

.property-badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.2;
  color: #111 !important;
  background: #f3eadc !important;
  border: 1px solid #c9ab85;
}

.property-badge-pattern {
  color: #fff !important;
  background: var(--accent-color, #2d2016) !important;
  border: none;
}

.panel-header {
  background: var(--accent-color, #2d2016);
  color: white;
  border-radius: 18px;
  padding: 18px;
  margin: -4px -4px 18px;
  box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}

.panel-header .panel-title {
  color: white;
}

.panel-header .panel-address {
  color: rgba(255,255,255,0.88);
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 18px 0;
}

.info-card {
  background: #fbf8f3;
  border: 1px solid #eee4d8;
  border-top: 4px solid var(--accent-color, #2d2016);
  border-radius: 14px;
  padding: 12px;
}

.info-label {
  font-size: 11px;
  color: #5f5146;
  font-weight: 700;
  margin-bottom: 5px;
}

.info-value {
  font-size: 15px;
  font-weight: 800;
  color: #1f1712;
}

.section-title {
  margin: 22px 0 10px;
  font-size: 15px;
  color: var(--accent-color);
}

.comment-box {
  background: #fff7e8;
  border: 1px solid #d7bea0;
  border-radius: 14px;
  padding: 13px;
  line-height: 1.7;
  color: #332820;
  font-size: 13px;
}

.link-button {
    display: block;
    padding: 10px 12px;
    margin-top: 8px;
    border-left: 4px solid var(--accent-color);
    background: rgba(0,0,0,0.03);
    border-radius: 8px;
    color: #222 !important;
    text-decoration: none;
    font-weight: 700;
}

.link-button:hover {
    text-decoration: underline;
}

.link-primary {
    background: transparent;
    color: #1f1f1f !important;
    border: none;
    box-shadow: none;
}

.link-secondary {
    background: transparent;
    color: #1f1f1f !important;
    border: none;
    box-shadow: none;
}

.link-secondary:hover {
  background: #cdb08b;
}

.leaflet-control-zoom {
  margin-top: 100px !important;
}

@media (max-width: 900px) {
  .topbar {
    top: 12px;
    left: 12px;
    right: 390px;
    height: 52px;
    padding: 0 16px;
  }


  .side-panel {
    left: 12px;
    right: 12px;
    bottom: 12px;
    top: auto;
    width: auto;
    max-height: 42vh;
    background: #efe5d6;
  }

  .legend-card {
    display: none;
  }
}
</style>
"""

    custom_js = """
(function bootEnhancedMap() {
  if (typeof L === "undefined" || typeof __MAP_NAME__ === "undefined") {
    setTimeout(bootEnhancedMap, 50);
    return;
  }
const propertyPoints = __POINTS_JSON__;
const patternColors = __PATTERN_COLORS__;

document.getElementById("totalCount").textContent = propertyPoints.length + "件";
document.getElementById("mapCount").textContent = propertyPoints.length + "件";

const legend = document.getElementById("legendItems");
Object.entries(patternColors).forEach(([label, color]) => {
  const item = document.createElement("div");
  item.className = "legend-item";
  item.innerHTML = `<span class="legend-dot" style="background:${color}"></span><span>${label}</span>`;
  legend.appendChild(item);
});

window.closePanel = function() {
    document.getElementById("sidePanel").innerHTML = `
        <div class="panel-empty">
            <h2>物件を選択してください</h2>
            <p>
                地図上の物件をクリックすると、
                詳細情報・事業成立性・営業シミュレーションへのリンクを表示します。
            </p>
        </div>
    `;
}

function safe(value) {
  if (value === null || value === undefined || value === "" || Number.isNaN(value)) return "-";
  return value;
}

function yen(value) {
  if (value === null || value === undefined || value === "" || Number.isNaN(value)) return "-";
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  return n.toLocaleString() + "円";
}

function renderPanel(p) {
  const accentColor = patternColors[p["事業成立パターン"]] || "#2d2016";
  document.getElementById("sidePanel").style.setProperty("--accent-color", accentColor);

  const simButton = p["営業シミュレーションURL"]
    ? `<a class="link-button link-primary" href="${p["営業シミュレーションURL"]}">営業シミュレーションを見る</a>`
    : "";

  const detailButton = p["詳細URL"]
    ? `<a class="link-button link-secondary" href="${p["詳細URL"]}" target="_blank">掲載元詳細ページを見る</a>`
    : "";

    const panel = document.getElementById("sidePanel");

    panel.style.setProperty(
        "--accent-color",
        patternColors[p["事業成立パターン"]] || "#666");

  document.getElementById("sidePanel").innerHTML = `
    <div class="panel-header">
    <button class="close-panel-btn" onclick="closePanel()">
      ✕
    </button>
        <h2 class="panel-title">${safe(p["物件名"])}</h2>
        <div class="panel-address">${safe(p["所在地"])}</div>
    </div>

      <div class="badges">
        <span class="property-badge property-badge-pattern">
            ${safe(p["事業成立パターン"])}
        </span>
        <span class="property-badge">${safe(p["飲食可否"])}</span>
        <span class="property-badge">${safe(p["評価ランク"])}</span>
      </div>

      <div class="info-grid">
        <div class="info-card">
          <div class="info-label">家賃</div>
          <div class="info-value">${safe(p["家賃"])}</div>
        </div>
        <div class="info-card">
          <div class="info-label">坪数</div>
          <div class="info-value">${safe(p["坪数"])}坪</div>
        </div>
        <div class="info-card">
          <div class="info-label">必要月商</div>
          <div class="info-value">${yen(p["必要月商"])}</div>
        </div>
        <div class="info-card">
          <div class="info-label">推奨必要日客数</div>
          <div class="info-value">${safe(p["推奨必要日客数"])}人</div>
        </div>
        <div class="info-card">
          <div class="info-label">初期投資中央値</div>
          <div class="info-value">${yen(p["初期投資中央値"])}</div>
        </div>
        <div class="info-card">
          <div class="info-label">立地区分</div>
          <div class="info-value">${safe(p["立地区分"])}</div>
        </div>
      </div>

      <h3 class="section-title">推奨カフェモデル</h3>
      <div class="comment-box">${safe(p["推奨カフェモデル"])}</div>

      <h3 class="section-title">ソンス評価</h3>
      <div class="info-grid">
        <div class="info-card">
          <div class="info-label">星評価</div>
          <div class="info-value">${safe(p["seongsu_fit_stars"])}</div>
        </div>
        <div class="info-card">
          <div class="info-label">スコア</div>
          <div class="info-value">${safe(p["seongsu_fit_score"])}</div>
        </div>
      </div>
      <div class="comment-box">${safe(p["seongsu_fit_comment"])}</div>

      <h3 class="section-title">評価コメント</h3>
      <div class="comment-box">${safe(p["評価コメント"])}</div>

      <h3 class="section-title">関連リンク</h3>
      ${simButton}
      ${detailButton}
    </div>
  `;
}

propertyPoints.forEach((p) => {
  const marker = L.circleMarker([p.latitude, p.longitude], {
    radius: 8,
    color: "#ffffff",
    weight: 2,
    fillColor: p.color,
    fillOpacity: 0.92
  }).addTo(__MAP_NAME__);

  marker.bindTooltip(p["物件名"], {
    direction: "top",
    sticky: true
  });

  marker.on("click", function() {
    renderPanel(p);
    __MAP_NAME__.panTo([p.latitude, p.longitude]);
  });
});

const params = new URLSearchParams(window.location.search);
const targetProperty = params.get("property");

if (targetProperty) {
  const decodedTarget = decodeURIComponent(targetProperty);
  const target = propertyPoints.find(p => p["物件名"] === decodedTarget);

  if (target) {
    renderPanel(target);
    __MAP_NAME__.setView([target.latitude, target.longitude], 17);
  }
}

})();
"""

    custom_js = custom_js.replace("__POINTS_JSON__", points_json)
    custom_js = custom_js.replace("__PATTERN_COLORS__", json.dumps(PATTERN_COLORS, ensure_ascii=False))
    custom_js = custom_js.replace("__MAP_NAME__", map_name)

    m.get_root().header.add_child(folium.Element(custom_css))
    m.get_root().html.add_child(folium.Element(custom_html))
    m.get_root().script.add_child(folium.Element(custom_js))

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FINAL_HTML.parent.mkdir(parents=True, exist_ok=True)

    m.save(OUTPUT_HTML)
    m.save(OUTPUT_FINAL_HTML)

    print(f"[LOAD] {INPUT_DASHBOARD}: {len(df)}件")
    print(f"[SAVE] {OUTPUT_HTML}")
    print(f"[SAVE] {OUTPUT_FINAL_HTML}")


if __name__ == "__main__":
    main()