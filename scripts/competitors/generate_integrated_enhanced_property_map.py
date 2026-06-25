from pathlib import Path
import json
import html

import folium
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DASHBOARD = (
    BASE_DIR
    / "output"
    / "archive_csv"
    / "cafe_business_dashboard.csv"
)
INPUT_BUSINESS_PLAN = (
    BASE_DIR
    / "output"
    / "competitors"
    / "business_plan_dashboard_with_competitors.csv"
)
INPUT_SIM_INDEX = BASE_DIR / "output" / "archive_csv" / "property_business_simulations_index.csv"

INPUT_COMPETITORS = (
    BASE_DIR
    / "data"
    / "competitors"
    / "competitors_master.csv"
)

INPUT_COMPETITOR_SUMMARY = (
    BASE_DIR
    / "output"
    / "competitors"
    / "property_competitor_summary.csv"
)

OUTPUT_HTML = (
    BASE_DIR
    / "output"
    / "competitors"
    / "integrated_property_map.html"
)

OUTPUT_FINAL_HTML = (
    BASE_DIR
    / "output"
    / "competitors"
    / "integrated_property_map.html"
)


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
        if col in [
            "営業シミュレーションURL",
            "ファイル名",
            "html_file",
            "simulation_file",
            "filename",
            "file_name",
        ]:
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
            col
            for col in [
                "物件名",
                "seongsu_fit_stars",
                "seongsu_fit_score",
                "seongsu_fit_type",
                "seongsu_fit_comment",
                "seongsu_rank",
                "nearby_500m_count",
                "nearby_1000m_count",
                "nearest_competitor_name",
                "nearest_competitor_distance_m",
            ]
            if col in bp.columns
        ]

        if "物件名" in bp_cols:
            bp = bp[bp_cols].drop_duplicates(subset=["物件名"], keep="first")

            # 既存CSV側に同名列がある場合でも _x/_y を作らない
            duplicate_cols = [col for col in bp_cols if col != "物件名" and col in df.columns]
            if duplicate_cols:
                df = df.drop(columns=duplicate_cols)

            df = df.merge(bp, on="物件名", how="left")
        if INPUT_COMPETITOR_SUMMARY.exists():
          summary = pd.read_csv(INPUT_COMPETITOR_SUMMARY)

          summary_cols = [
              col
              for col in [
                  "物件名",
                  "nearby_500m_count",
                  "nearby_1000m_count",
                  "nearest_competitor_name",
                  "nearest_competitor_distance_m",
              ]
              if col in summary.columns
          ]

          if "物件名" in summary_cols:
              summary = summary[summary_cols].drop_duplicates(subset=["物件名"], keep="first")

              duplicate_cols = [
                  col for col in summary_cols
                  if col != "物件名" and col in df.columns
              ]
              if duplicate_cols:
                  df = df.drop(columns=duplicate_cols)

              df = df.merge(summary, on="物件名", how="left")

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
            "nearby_500m_count": clean_value(row.get("nearby_500m_count")),
            "nearby_1000m_count": clean_value(row.get("nearby_1000m_count")),
            "nearest_competitor_name": clean_value(row.get("nearest_competitor_name")),
            "nearest_competitor_distance_m": clean_value(row.get("nearest_competitor_distance_m")),
            "color": color,
        })

    return points


def make_competitor_points():
    if not INPUT_COMPETITORS.exists():
        print(f"[WARN] 競合CSVがありません: {INPUT_COMPETITORS}")
        return []

    competitors = pd.read_csv(INPUT_COMPETITORS, dtype=str).fillna("")

    points = []

    for _, row in competitors.iterrows():
        lat = to_float(row.get("lat"))
        lng = to_float(row.get("lng"))

        if lat is None or lng is None:
            continue

        points.append(
            {
                "name": row.get("store_name", ""),
                "genre": row.get("genre", ""),
                "address": row.get("address", ""),
                "rating": row.get("rating", ""),
                "review_count": row.get("review_count", ""),
                "url": row.get("url", ""),
                "lat": lat,
                "lng": lng,
                "source": str(row.get("source", "")),
                "linked_site_name": row.get("linked_site_name", ""),
            }
        )

    print(f"[LOAD] competitors: {INPUT_COMPETITORS} / {len(competitors)} rows")
    print(f"[PLOT] competitors: {len(points)} rows")

    return points


def to_float(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def main():
    df = load_data()
    points = make_points(df)
    competitor_points = make_competitor_points()

    m = folium.Map(
        location=[34.3428, 134.0466],
        zoom_start=13,
        tiles="CartoDB Voyager",
        control_scale=True,
    )

    map_name = m.get_name()
    points_json = json.dumps(points, ensure_ascii=False)
    competitor_points_json = json.dumps(competitor_points, ensure_ascii=False)

    custom_html = """
<div class="suumo-like-topbar">
  <div class="topbar-brand-block">
    <div class="brand">☕ Takamatsu Cafe Project</div>
    <div class="subtitle">高松市 カフェ開業候補地マップ｜物件・競合統合版</div>
  </div>

  <div class="topbar-nav-block">
    <div class="topbar-filter-block topbar-count-block">
      <div class="topbar-filter-title">表示物件</div>
      <div class="topbar-filter-value" id="totalCount">-</div>
    </div>

    <div class="topbar-filter-block topbar-count-block">
      <div class="topbar-filter-title">競合店舗</div>
      <div class="topbar-filter-value" id="competitorCount">-</div>
    </div>

    <div class="topbar-filter-block topbar-dropdown-block">
      <button class="topbar-dropdown-button" onclick="toggleTopbarDropdown('sourceDropdown')">
        競合ソース ▾
      </button>
      <div class="topbar-dropdown-content" id="sourceDropdown">
        <div class="dropdown-section-title">競合データソース</div>
        <div class="source-list" id="sourceList"></div>
      </div>
    </div>

    <div class="topbar-filter-block topbar-dropdown-block topbar-pattern-block">
      <button class="topbar-dropdown-button" onclick="toggleTopbarDropdown('patternDropdown')">
        事業成立パターン ▾
      </button>
      <div class="topbar-dropdown-content pattern-dropdown-content" id="patternDropdown">
        <div class="dropdown-section-title">事業成立パターン凡例</div>
        <div class="pattern-strip pattern-strip-dropdown" id="legendItems"></div>
      </div>
    </div>
  </div>
</div>

<div class="competitor-panel" id="competitorPanel"></div>
<div class="side-panel" id="sidePanel"></div>
"""

    custom_css = """
<style>
* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.leaflet-container {
  background: #f7f2ea;
}

.suumo-like-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 68px;
  z-index: 9999;
  background: #fff;
  border: 1px solid #ddd;
  border-bottom: 3px solid #2f8f2f;
  display: flex;
  align-items: stretch;
  box-sizing: border-box;
}

.topbar-brand-block {
  width: 300px;
  padding: 12px 20px;
  border-right: 1px solid #ddd;
  box-sizing: border-box;
}

.brand {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
}

.subtitle {
  margin-top: 6px;
  font-size: 11px;
  color: #555;
  line-height: 1.3;
}

.topbar-nav-block {
  flex: 1;
  display: flex;
  align-items: stretch;
  overflow: hidden;
}

.topbar-filter-block {
  min-width: 118px;
  padding: 10px 14px;
  border-right: 1px solid #ddd;
  text-align: center;
  box-sizing: border-box;
}

.topbar-filter-title {
  font-size: 12px;
  font-weight: 700;
  color: #2f8f2f;
  line-height: 1.2;
  white-space: nowrap;
}

.topbar-filter-value {
  margin-top: 6px;
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
}

.topbar-count-block {
  min-width: 120px;
}

.topbar-dropdown-block {
  position: relative;
  min-width: 170px;
  padding: 0;
  text-align: left;
}

.topbar-pattern-block {
  min-width: 190px;
  max-width: none;
}

.topbar-dropdown-button {
  width: 100%;
  height: 100%;
  padding: 0 18px;
  border: none;
  background: #fff;
  color: #2f8f2f;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.topbar-dropdown-button:hover {
  background: #f6faf6;
}

.dropdown-arrow {
  font-size: 11px;
  color: #5f8f2f;
}

.topbar-dropdown-content {
  display: none;
  position: absolute;
  top: 68px;
  left: 0;
  min-width: 230px;
  max-width: 360px;
  max-height: 420px;
  overflow-y: auto;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #ddd;
  border-top: 3px solid #2f8f2f;
  box-shadow: 0 8px 20px rgba(0,0,0,0.14);
  z-index: 10001;
  font-size: 13px;
  line-height: 1.7;
  color: #333;
}

.topbar-dropdown-content.is-open {
  display: block;
}

.pattern-dropdown-content {
  min-width: 320px;
}

.dropdown-section-title {
  margin-bottom: 8px;
  color: #2f8f2f;
  font-size: 12px;
  font-weight: 800;
}

.suumo-like-topbar {
  pointer-events: auto;
}

.topbar-dropdown-block,
.topbar-dropdown-button,
.topbar-dropdown-content {
  pointer-events: auto;
}

.topbar-dropdown-content.is-open {
  display: block;
}

.source-list {
  display: grid;
  gap: 6px;
}

.source-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.source-row:last-child {
  border-bottom: none;
}

.source-name {
  font-weight: 700;
}

.source-count {
  font-weight: 800;
}

.pattern-legend {
  margin-top: 5px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 11px;
  line-height: 1.2;
}

.pattern-strip {
  display: flex;
  align-items: center;
  gap: 7px;
  overflow-x: auto;
  padding: 2px 2px 6px;
  scrollbar-width: thin;
}

.pattern-strip-dropdown {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
  overflow-x: visible;
  padding: 0;
}

.pattern-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex: 0 0 auto;
  max-width: 160px;
  padding: 5px 8px;
  border-radius: 999px;
  background: #f7f2ea;
  border: 1px solid #e4d7c6;
  color: #34281f;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.pattern-chip-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.legend-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.06);
}

.competitor-panel,
.side-panel {
  display: none;
  position: fixed;
  z-index: 10000;
  top: 104px;
  bottom: 0;
  height: calc(100% - 104px);
  max-height: none;
  background: rgba(255,255,255,0.97);
  box-shadow: 1px 4px 12px 2px rgba(0,0,0,0.18);
  overflow-y: auto;
  backdrop-filter: blur(12px);
}

.competitor-panel {
  left: 0;
  right: auto;
  width: 300px;
  border-radius: 0 18px 18px 0;
}

.side-panel {
  left: auto;
  right: 0;
  width: 360px;
  border-radius: 18px 0 0 18px;
  box-shadow: -1px 4px 12px 2px rgba(0,0,0,0.18);
}

.panel-empty {
  padding: 28px;
  color: #4a4037;
  line-height: 1.8;
}

.panel-empty h2 {
  font-size: 17px;
  margin: 0 0 10px;
  color: #2d241c;
}

.close-panel-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255,255,255,0.25);
  color: white;
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
  transition: .2s;
}

.close-panel-btn:hover {
  background: rgba(255,255,255,0.45);
}

.panel-header {
  position: relative;
  background: var(--accent-color, #2d2016);
  color: white;
  border-radius: 18px;
  padding: 18px 54px 18px 18px;
  margin: 18px 18px 16px;
  box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}

.panel-title {
  margin: 0;
  color: white;
  font-size: 20px;
  line-height: 1.35;
}

.panel-address {
  color: rgba(255,255,255,0.88);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 6px;
}

.panel-body {
  padding: 0 18px 22px;
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

.leaflet-control-zoom {
  margin-top: 96px !important;
}

.competitor-coffee-icon {
  background: transparent !important;
  border: none !important;
}

.competitor-marker-inner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(185, 28, 28, 0.70);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,.15);
  border: 1px solid rgba(255,255,255,0.8);
}

@media (max-width: 1100px) {
  .suumo-like-topbar {
    grid-template-columns: 260px 1fr;
  }

  .topbar-nav-block {
    grid-template-columns: 105px 105px 1fr;
  }

  .competitor-panel {
    width: 280px;
  }

  .side-panel {
    width: 330px;
  }
}

@media (max-width: 900px) {
  .suumo-like-topbar {
    min-height: 76px;
    grid-template-columns: 1fr;
  }

  .topbar-brand-block {
    padding: 10px 14px 4px;
    border-right: none;
  }

  .brand {
    font-size: 15px;
  }

  .subtitle {
    font-size: 10px;
  }

  .topbar-nav-block {
    grid-template-columns: 82px 82px 1fr;
  }

  .topbar-filter-block {
    padding: 6px 8px;
  }

  .topbar-filter-title {
    font-size: 10px;
  }

  .topbar-filter-value {
    font-size: 13px;
  }

  .pattern-chip {
    font-size: 10px;
    max-width: 120px;
    padding: 4px 7px;
  }

  .competitor-panel {
    top: 96px;
    left: 0;
    right: 0;
    bottom: auto;
    width: 100%;
    height: auto;
    max-height: 32vh;
    border-radius: 0 0 18px 18px;
  }

  .side-panel {
    top: auto;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: auto;
    max-height: 42vh;
    border-radius: 18px 18px 0 0;
  }

  .leaflet-control-zoom {
    margin-top: 126px !important;
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
  const competitors = __COMPETITORS__;

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  setText("totalCount", propertyPoints.length + "件");
  setText("competitorCount", competitors.length + "件");

  const sourceLabels = {
    tabelog: "食べログ",
    hotpepper: "ホットペッパー",
    google_maps: "Googleマップ"
  };

  const sourceCounts = {};
  competitors.forEach((c) => {
    const key = String(c.source || "unknown").toLowerCase().trim() || "unknown";
    sourceCounts[key] = (sourceCounts[key] || 0) + 1;
  });

  const sourceList = document.getElementById("sourceList");
  if (sourceList) {
    Object.entries(sourceCounts).forEach(([source, count]) => {
      const row = document.createElement("div");
      row.className = "source-row";
      row.innerHTML =
        '<span class="source-name">' + (sourceLabels[source] || source) + '</span>' +
        '<span class="source-count">' + count + '件</span>';
      sourceList.appendChild(row);
    });
  }

  const legend = document.getElementById("legendItems");
  if (legend) {
    Object.entries(patternColors).forEach(([label, color]) => {
      const item = document.createElement("div");
      item.className = "pattern-chip";
      item.innerHTML =
        '<span class="legend-dot" style="background:' + color + '"></span>' +
        '<span class="pattern-chip-label">' + label + '</span>';
      legend.appendChild(item);
    });
  }

  window.toggleTopbarDropdown = function(id) {
    const target = document.getElementById(id);
    if (!target) return;

    document.querySelectorAll(".topbar-dropdown-content").forEach(function(el) {
      if (el.id !== id) {
        el.classList.remove("is-open");
      }
    });

    target.classList.toggle("is-open");
  };

  document.addEventListener("click", function(event) {
    if (!event.target.closest(".topbar-dropdown-block")) {
      document.querySelectorAll(".topbar-dropdown-content").forEach(function(el) {
        el.classList.remove("is-open");
      });
    }
  });

  window.closePropertyPanel = function() {
    document.getElementById("sidePanel").style.display = "none";
  };

  window.closeCompetitorPanel = function() {
    document.getElementById("competitorPanel").style.display = "none";
  };

  window.toggleTopbarDropdown = function(id) {
  const target = document.getElementById(id);
  if (!target) return;

  document.querySelectorAll(".topbar-dropdown-content").forEach(function(el) {
    if (el.id !== id) {
      el.classList.remove("is-open");
    }
  });

  target.classList.toggle("is-open");
};

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
    const sidePanel = document.getElementById("sidePanel");
    sidePanel.style.display = "block";
    sidePanel.style.setProperty("--accent-color", accentColor);

    const simButton = p["営業シミュレーションURL"]
      ? '<a class="link-button link-primary" href="' + p["営業シミュレーションURL"] + '">営業シミュレーションを見る</a>'
      : "";

    const detailButton = p["詳細URL"]
      ? '<a class="link-button link-secondary" href="' + p["詳細URL"] + '" target="_blank" rel="noopener">掲載元詳細ページを見る</a>'
      : "";

    sidePanel.innerHTML =
      '<div class="panel-header">' +
        '<button class="close-panel-btn" onclick="closePropertyPanel()">✕</button>' +
        '<h2 class="panel-title">' + safe(p["物件名"]) + '</h2>' +
        '<div class="panel-address">' + safe(p["所在地"]) + '</div>' +
      '</div>' +
      '<div class="panel-body">' +
        '<div class="badges">' +
          '<span class="property-badge property-badge-pattern">' + safe(p["事業成立パターン"]) + '</span>' +
          '<span class="property-badge">' + safe(p["飲食可否"]) + '</span>' +
          '<span class="property-badge">' + safe(p["評価ランク"]) + '</span>' +
        '</div>' +

        '<div class="info-grid">' +
          '<div class="info-card"><div class="info-label">家賃</div><div class="info-value">' + safe(p["家賃"]) + '</div></div>' +
          '<div class="info-card"><div class="info-label">坪数</div><div class="info-value">' + safe(p["坪数"]) + '坪</div></div>' +
          '<div class="info-card"><div class="info-label">必要月商</div><div class="info-value">' + yen(p["必要月商"]) + '</div></div>' +
          '<div class="info-card"><div class="info-label">推奨必要日客数</div><div class="info-value">' + safe(p["推奨必要日客数"]) + '人</div></div>' +
          '<div class="info-card"><div class="info-label">初期投資中央値</div><div class="info-value">' + yen(p["初期投資中央値"]) + '</div></div>' +
          '<div class="info-card"><div class="info-label">立地区分</div><div class="info-value">' + safe(p["立地区分"]) + '</div></div>' +
        '</div>' +

        '<h3 class="section-title">近隣競合</h3>' +
        '<div class="info-grid">' +
          '<div class="info-card"><div class="info-label">500m以内</div><div class="info-value">' + safe(p["nearby_500m_count"]) + '件</div></div>' +
          '<div class="info-card"><div class="info-label">1km以内</div><div class="info-value">' + safe(p["nearby_1000m_count"]) + '件</div></div>' +
          '<div class="info-card"><div class="info-label">最寄競合</div><div class="info-value">' + safe(p["nearest_competitor_name"]) + '</div></div>' +
          '<div class="info-card"><div class="info-label">距離</div><div class="info-value">' + safe(p["nearest_competitor_distance_m"]) + 'm</div></div>' +
        '</div>' +

        '<h3 class="section-title">推奨カフェモデル</h3>' +
        '<div class="comment-box">' + safe(p["推奨カフェモデル"]) + '</div>' +

        '<h3 class="section-title">ソンス評価</h3>' +
        '<div class="info-grid">' +
          '<div class="info-card"><div class="info-label">星評価</div><div class="info-value">' + safe(p["seongsu_fit_stars"]) + '</div></div>' +
          '<div class="info-card"><div class="info-label">スコア</div><div class="info-value">' + safe(p["seongsu_fit_score"]) + '</div></div>' +
        '</div>' +
        '<div class="comment-box">' + safe(p["seongsu_fit_comment"]) + '</div>' +

        '<h3 class="section-title">評価コメント</h3>' +
        '<div class="comment-box">' + safe(p["評価コメント"]) + '</div>' +

        '<h3 class="section-title">関連リンク</h3>' +
        simButton +
        detailButton +
      '</div>';
  }

  function renderCompetitorPanel(c) {
    const competitorPanel = document.getElementById("competitorPanel");
    competitorPanel.style.display = "block";
    competitorPanel.style.setProperty("--accent-color", "#7f1d1d");

    const source = String(c.source || "").toLowerCase().trim();

    let sourceLabel = "食べログ";
    if (source === "hotpepper") {
      sourceLabel = "ホットペッパー";
    } else if (source === "google_maps") {
      sourceLabel = "Googleマップ";
    }

    const linkedSiteName = String(c.linked_site_name || "").trim();

    const buttonLabel = linkedSiteName
      ? linkedSiteName
      : sourceLabel;

    const urlButton = c.url
      ? '<a class="link-button link-primary" href="' + c.url + '" target="_blank" rel="noopener">' + buttonLabel + 'を見る</a>'
      : "";

    competitorPanel.innerHTML =
      '<div class="panel-header">' +
        '<button class="close-panel-btn" onclick="closeCompetitorPanel()">✕</button>' +
        '<h2 class="panel-title">' + safe(c.name) + '</h2>' +
        '<div class="panel-address">' + safe(c.address) + '</div>' +
      '</div>' +
      '<div class="panel-body">' +
        '<div class="badges">' +
          '<span class="property-badge property-badge-pattern">競合店舗</span>' +
          '<span class="property-badge">' + sourceLabel + '</span>' +
        '</div>' +
        '<h3 class="section-title">店舗ジャンル</h3>' +
        '<div class="comment-box">' + safe(c.genre) + '</div>' +
        '<div class="info-grid">' +
          '<div class="info-card"><div class="info-label">評価</div><div class="info-value">' + safe(c.rating) + '</div></div>' +
          '<div class="info-card"><div class="info-label">口コミ数</div><div class="info-value">' + safe(c.review_count) + '</div></div>' +
        '</div>' +
        '<h3 class="section-title">関連リンク</h3>' +
        urlButton +
      '</div>';
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

  const coffeeIcon = L.divIcon({
    className: "competitor-coffee-icon",
    html: '<div class="competitor-marker-inner">☕</div>',
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -9]
  });

  competitors.forEach((c) => {
    if (!c.lat || !c.lng) return;

    L.marker([Number(c.lat), Number(c.lng)], { icon: coffeeIcon, zIndexOffset: 1000 })
      .bindTooltip(c.name || "競合店舗", {
        direction: "top",
        sticky: true
      })
      .on("click", function() {
        renderCompetitorPanel(c);
        __MAP_NAME__.panTo([Number(c.lat), Number(c.lng)]);
      })
      .addTo(__MAP_NAME__);
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
    custom_js = custom_js.replace("__COMPETITORS__", competitor_points_json)

    m.get_root().header.add_child(folium.Element(custom_css))
    m.get_root().html.add_child(folium.Element(custom_html))
    m.get_root().script.add_child(folium.Element(custom_js))

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FINAL_HTML.parent.mkdir(parents=True, exist_ok=True)

    m.save(OUTPUT_HTML)
    m.save(OUTPUT_FINAL_HTML)

    print(f"[LOAD] {INPUT_DASHBOARD}: {len(df)}件")
    print(f"[PLOT] properties: {len(points)} rows")
    print(f"[PLOT] competitors: {len(competitor_points)} rows")
    print(f"[SAVE] {OUTPUT_HTML}")
    print(f"[SAVE] {OUTPUT_FINAL_HTML}")


if __name__ == "__main__":
    main()
