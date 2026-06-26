from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_PATH = BASE_DIR / "output" / "master" / "supplier_map_targets_geocoded.csv"
OUT_DIR = BASE_DIR / "output" / "dashboard"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_LABELS = {
    "fruit": "フルーツ",
    "coffee": "コーヒー",
    "consumables": "消耗品",
    "materials": "原材料",
    "ice": "氷",
}

df = pd.read_csv(IN_PATH, encoding="utf-8-sig").fillna("")
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"]).copy()

records = df.to_dict(orient="records")

html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>仕入れ先マップ</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
body {{
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f4ef;
  color: #222;
}}
header {{
  background: #2f241d;
  color: white;
  padding: 14px 20px;
}}
header h1 {{
  margin: 0;
  font-size: 22px;
}}
header p {{
  margin: 4px 0 0;
  color: #ddd;
  font-size: 13px;
}}
.layout {{
  display: grid;
  grid-template-columns: 460px 1fr;
  height: calc(100vh - 72px);
}}
.left {{
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ddd;
  background: #fff;
  min-width: 0;
}}
.controls {{
  padding: 12px;
  border-bottom: 1px solid #eee;
}}
.search {{
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  margin-bottom: 10px;
}}
.filters {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}}
.filter {{
  border: 1px solid #ddd;
  border-radius: 999px;
  padding: 6px 10px;
  background: #fafafa;
  cursor: pointer;
  font-size: 13px;
}}
.filter.active {{
  background: #2f241d;
  color: white;
}}
.summary {{
  margin-top: 10px;
  color: #666;
  font-size: 13px;
}}
.list {{
  overflow-y: auto;
  padding: 10px;
  flex: 1;
  scroll-behavior: smooth;
}}
.item {{
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  background: #fff;
}}
.item:hover {{
  background: #faf6f0;
}}
.item.active {{
  border-color: #2f241d;
  background: #f4ede4;
  box-shadow: 0 2px 8px rgba(47,36,29,.18);
}}
.item-title {{
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 6px;
}}
.badge {{
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  background: #eee2d2;
  font-size: 12px;
  margin-right: 4px;
  margin-bottom: 4px;
}}
.items {{
  margin-top: 10px;
  line-height: 1.55;
  font-size: 14px;
}}
.notes {{
  margin-top: 8px;
  line-height: 1.55;
  font-size: 14px;
}}
.links {{
  margin-top: 10px;
  font-size: 14px;
}}
.addr {{
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}}
.right {{
  display: grid;
  grid-template-rows: 1fr 250px;
  min-width: 0;
}}
#map {{
  width: 100%;
  height: 100%;
}}
.detail {{
  background: #fff;
  border-top: 1px solid #ddd;
  padding: 14px;
  overflow-y: auto;
}}
.detail h2 {{
  margin: 0 0 8px;
  font-size: 20px;
}}
.detail-grid {{
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 6px 12px;
  font-size: 14px;
}}
.label {{
  color: #777;
}}
a {{
  color: #0645ad;
}}
.empty {{
  color: #777;
  padding: 16px;
}}
.leaflet-popup-content {{
  font-size: 13px;
  line-height: 1.45;
}}
</style>
</head>
<body>
<header>
  <h1>仕入れ先マップ</h1>
  <p>ローカル仕入先48件。地図は補助、検索・一覧・詳細確認を主役にした画面です。</p>
</header>

<div class="layout">
  <section class="left">
    <div class="controls">
      <input id="searchBox" class="search" placeholder="名称・住所・取扱商品・メモで検索">
      <div class="filters">
        <button class="filter active" data-category="all">すべて</button>
        <button class="filter" data-category="fruit">フルーツ</button>
        <button class="filter" data-category="coffee">コーヒー</button>
        <button class="filter" data-category="consumables">消耗品</button>
        <button class="filter" data-category="materials">原材料</button>
        <button class="filter" data-category="ice">氷</button>
      </div>
      <div class="summary" id="summary"></div>
    </div>
    <div class="list" id="supplierList"></div>
  </section>

  <section class="right">
    <div id="map"></div>
    <div class="detail" id="detail">
      <div class="empty">左の一覧または地図上のピンから仕入先を選択してください。</div>
    </div>
  </section>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const suppliers = {json.dumps(records, ensure_ascii=False)};
const categoryLabels = {json.dumps(CATEGORY_LABELS, ensure_ascii=False)};

let currentCategory = "all";
let selectedId = null;
let markers = new Map();
let currentList = [];
let suppressFit = false;

const map = L.map("map").setView([34.34, 134.05], 11);

L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors"
}}).addTo(map);

function label(cat) {{
  return categoryLabels[cat] || cat || "";
}}

function textOf(s) {{
  return Object.values(s).join(" ").toLowerCase();
}}

function filteredSuppliers() {{
  const q = document.getElementById("searchBox").value.toLowerCase().trim();

  return suppliers.filter(s => {{
    const catOk = currentCategory === "all" || s.source_category === currentCategory;
    const qOk = !q || textOf(s).includes(q);
    return catOk && qOk;
  }});
}}

function popupHtml(s) {{
  return `
    <strong>${{s.name}}</strong><br>
    <span>${{label(s.source_category)}} / ${{s.type || ""}}</span><br>
    <span>${{s.address_candidate || ""}}</span>
  `;
}}

function cardHtml(s) {{
  return `
    <div class="item ${{s.supplier_id === selectedId ? "active" : ""}}" id="card-${{s.supplier_id}}" onclick="selectSupplier('${{s.supplier_id}}', true)">
      <div class="item-title">${{s.name}}</div>
      <div>
        <span class="badge">${{label(s.source_category)}}</span>
        <span class="badge">${{s.type || ""}}</span>
        <span class="badge">${{s.local_or_online || ""}}</span>
      </div>
      <div class="items">${{s.main_items || ""}}</div>
      <div class="notes">${{s.notes || ""}}</div>
      <div class="links">
        ${{s.official_url ? `<a href="${{s.official_url}}" target="_blank" onclick="event.stopPropagation()">公式サイト</a>` : ""}}
        ${{s.google_maps_url ? ` / <a href="${{s.google_maps_url}}" target="_blank" onclick="event.stopPropagation()">Google Maps</a>` : ""}}
      </div>
      <div class="addr">${{s.address_candidate || ""}}</div>
    </div>
  `;
}}

function renderMarkers(list, fitMap = true) {{
  markers.forEach(marker => map.removeLayer(marker));
  markers.clear();

  const bounds = [];

  list.forEach(s => {{
    const lat = Number(s.latitude);
    const lng = Number(s.longitude);
    if (!isFinite(lat) || !isFinite(lng)) return;

    const marker = L.marker([lat, lng]).addTo(map).bindPopup(popupHtml(s));
    marker.on("click", () => selectSupplier(s.supplier_id, false));
    markers.set(s.supplier_id, marker);
    bounds.push([lat, lng]);
  }});

  if (fitMap && bounds.length) {{
    map.fitBounds(bounds, {{ padding: [30, 30], maxZoom: 13 }});
  }}
}}

function renderList(list) {{
  currentList = list;

  document.getElementById("summary").textContent =
    `${{list.length}}件表示 / 全${{suppliers.length}}件`;

  document.getElementById("supplierList").innerHTML =
    list.map(cardHtml).join("") || `<div class="empty">該当する仕入先がありません。</div>`;
}}

function renderDetail(s) {{
  if (!s) {{
    document.getElementById("detail").innerHTML =
      `<div class="empty">左の一覧または地図上のピンから仕入先を選択してください。</div>`;
    return;
  }}

  document.getElementById("detail").innerHTML = `
    <h2>${{s.name}}</h2>
    <div class="detail-grid">
      <div class="label">カテゴリ</div><div>${{label(s.source_category)}}</div>
      <div class="label">分類</div><div>${{s.type || ""}}</div>
      <div class="label">住所</div><div>${{s.address_candidate || ""}}</div>
      <div class="label">取扱</div><div>${{s.main_items || ""}}</div>
      <div class="label">メモ</div><div>${{s.notes || ""}}</div>
      <div class="label">公式</div><div>${{s.official_url ? `<a href="${{s.official_url}}" target="_blank">公式サイト</a>` : ""}}</div>
      <div class="label">Google</div><div>${{s.google_maps_url ? `<a href="${{s.google_maps_url}}" target="_blank">Google Maps</a>` : ""}}</div>
    </div>
  `;
}}

function scrollToCard(id) {{
  const card = document.getElementById(`card-${{id}}`);
  if (card) {{
    card.scrollIntoView({{ behavior: "smooth", block: "center" }});
  }}
}}

function selectSupplier(id, moveMap = true) {{
  selectedId = id;
  const s = suppliers.find(x => x.supplier_id === id);
  if (!s) return;

  renderList(currentList);
  renderDetail(s);

  if (!moveMap) {{
    scrollToCard(id);
  }}

  const marker = markers.get(id);
  if (marker) {{
    if (moveMap) {{
      map.setView(marker.getLatLng(), 15);
    }}
    marker.openPopup();
  }}
}}

function renderAll(fitMap = true) {{
  selectedId = null;
  const list = filteredSuppliers();
  renderList(list);
  renderMarkers(list, fitMap);
  renderDetail(null);
}}

document.querySelectorAll(".filter").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".filter").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentCategory = btn.dataset.category;
    renderAll(true);
  }});
}});

document.getElementById("searchBox").addEventListener("input", () => {{
  renderAll(true);
}});

renderAll(true);
</script>
</body>
</html>
"""

(OUT_DIR / "procurement_supplier_map.html").write_text(html, encoding="utf-8")
print("[SAVE] output/dashboard/procurement_supplier_map.html")
print("[ROWS]", len(records))