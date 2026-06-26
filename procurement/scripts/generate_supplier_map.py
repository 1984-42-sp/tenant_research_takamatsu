from pathlib import Path
import json
import math

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

SUPPLIER_MASTER_PATH = BASE_DIR / "output" / "master" / "supplier_master.csv"
GEOCODED_PATH = BASE_DIR / "output" / "master" / "supplier_map_targets_geocoded.csv"

OUT_DIR = BASE_DIR / "output" / "dashboard"
OUT_PATH = OUT_DIR / "procurement_supplier_map.html"

CATEGORY_LABELS = {
    "fruit": "フルーツ",
    "coffee": "コーヒー",
    "consumables": "消耗品",
    "materials": "原材料",
    "ice": "氷",
}

OUTPUT_COLUMNS = [
    "supplier_id",
    "source_category",
    "name",
    "type",
    "local_or_online",
    "address_candidate",
    "latitude",
    "longitude",
    "official_url",
    "google_maps_url",
    "main_items",
    "notes",
]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"入力CSVが見つかりません: {path}")

    return pd.read_csv(path, encoding="utf-8-sig").fillna("")


def normalize_id(value) -> str:
    return str(value or "").strip()


def is_online(value) -> bool:
    text = str(value or "").strip().lower()
    return "オンライン" in text or text == "online"


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def load_coordinate_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["supplier_id", "latitude", "longitude", "google_maps_url"])

    coord_df = read_csv(path)
    coord_df = ensure_columns(coord_df, ["supplier_id", "latitude", "longitude", "google_maps_url"])
    coord_df["supplier_id"] = coord_df["supplier_id"].map(normalize_id)
    coord_df["latitude"] = pd.to_numeric(coord_df["latitude"], errors="coerce")
    coord_df["longitude"] = pd.to_numeric(coord_df["longitude"], errors="coerce")

    coord_df = coord_df[coord_df["supplier_id"] != ""].copy()
    coord_df = coord_df.drop_duplicates(subset=["supplier_id"], keep="last")

    return coord_df[["supplier_id", "latitude", "longitude", "google_maps_url"]]


def build_supplier_records() -> tuple[list[dict], dict]:
    master_df = read_csv(SUPPLIER_MASTER_PATH)
    master_df = ensure_columns(master_df, OUTPUT_COLUMNS)

    master_df["supplier_id"] = master_df["supplier_id"].map(normalize_id)
    master_df["local_or_online"] = master_df["local_or_online"].map(
        lambda v: "オンライン" if is_online(v) else (str(v or "").strip() or "ローカル")
    )

    coord_df = load_coordinate_table(GEOCODED_PATH)

    df = master_df.merge(
        coord_df,
        on="supplier_id",
        how="left",
        suffixes=("", "_geocoded"),
    )

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df["latitude"] = df["latitude"].where(df["latitude"].notna(), df["latitude_geocoded"])
    df["longitude"] = df["longitude"].where(df["longitude"].notna(), df["longitude_geocoded"])

    if "google_maps_url_geocoded" in df.columns:
        df["google_maps_url"] = df["google_maps_url"].where(
            df["google_maps_url"].astype(str).str.strip() != "",
            df["google_maps_url_geocoded"].fillna(""),
        )

    online_mask = df["local_or_online"].map(is_online)

    # オンライン仕入先は、一覧・詳細には出すがマーカー対象からは明確に除外する。
    df.loc[online_mask, "latitude"] = pd.NA
    df.loc[online_mask, "longitude"] = pd.NA
    df.loc[online_mask, "address_candidate"] = "オンライン"
    df.loc[online_mask, "google_maps_url"] = ""

    df = ensure_columns(df, OUTPUT_COLUMNS)

    records = []
    seen_uids: dict[str, int] = {}

    for idx, row in df.reset_index(drop=True).iterrows():
        record = {}
        for col in OUTPUT_COLUMNS:
            value = row.get(col, "")
            if col in ["latitude", "longitude"]:
                num = pd.to_numeric(value, errors="coerce")
                record[col] = float(num) if pd.notna(num) and math.isfinite(float(num)) else None
            else:
                record[col] = "" if pd.isna(value) else str(value).strip()

        base_uid = record["supplier_id"] or f"ROW{idx + 1:04d}"
        seen_uids[base_uid] = seen_uids.get(base_uid, 0) + 1
        record["_uid"] = base_uid if seen_uids[base_uid] == 1 else f"{base_uid}_{seen_uids[base_uid]}"

        records.append(record)

    marker_count = sum(
        1
        for r in records
        if not is_online(r.get("local_or_online"))
        and isinstance(r.get("latitude"), float)
        and isinstance(r.get("longitude"), float)
    )
    online_count = sum(1 for r in records if is_online(r.get("local_or_online")))

    stats = {
        "total": len(records),
        "marker_count": marker_count,
        "online_count": online_count,
        "local_count": len(records) - online_count,
    }

    return records, stats


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>仕入れ先マップ</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f4ef;
  color: #222;
}
header {
  background: #2f241d;
  color: white;
  padding: 14px 20px;
}
header h1 {
  margin: 0;
  font-size: 22px;
}
header p {
  margin: 4px 0 0;
  color: #ddd;
  font-size: 13px;
}
.layout {
  display: grid;
  grid-template-columns: 460px 1fr;
  height: calc(100vh - 72px);
}
.left {
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ddd;
  background: #fff;
  min-width: 0;
}
.controls {
  padding: 12px;
  border-bottom: 1px solid #eee;
}
.search {
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  margin-bottom: 10px;
}
.filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.filter {
  border: 1px solid #ddd;
  border-radius: 999px;
  padding: 6px 10px;
  background: #fafafa;
  cursor: pointer;
  font-size: 13px;
}
.filter.active {
  background: #2f241d;
  color: white;
}
.summary {
  margin-top: 10px;
  color: #666;
  font-size: 13px;
}
.list {
  overflow-y: auto;
  padding: 10px;
  flex: 1;
  scroll-behavior: smooth;
}
.item {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  background: #fff;
}
.item:hover {
  background: #faf6f0;
}
.item.active {
  border-color: #2f241d;
  background: #f4ede4;
  box-shadow: 0 2px 8px rgba(47,36,29,.18);
}
.item-title {
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 6px;
}
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  background: #eee2d2;
  font-size: 12px;
  margin-right: 4px;
  margin-bottom: 4px;
}
.badge.online {
  background: #dde7f7;
}
.items {
  margin-top: 10px;
  line-height: 1.55;
  font-size: 14px;
}
.notes {
  margin-top: 8px;
  line-height: 1.55;
  font-size: 14px;
}
.links {
  margin-top: 10px;
  font-size: 14px;
}
.addr {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}
.right {
  display: grid;
  grid-template-rows: 1fr 250px;
  min-width: 0;
}
#map {
  width: 100%;
  height: 100%;
}
.detail {
  background: #fff;
  border-top: 1px solid #ddd;
  padding: 14px;
  overflow-y: auto;
}
.detail h2 {
  margin: 0 0 8px;
  font-size: 20px;
}
.detail-grid {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 6px 12px;
  font-size: 14px;
}
.label {
  color: #777;
}
a {
  color: #0645ad;
}
.empty {
  color: #777;
  padding: 16px;
}
.leaflet-popup-content {
  font-size: 13px;
  line-height: 1.45;
}
</style>
</head>
<body>
<header>
  <h1>仕入れ先マップ</h1>
  <p>取得済み仕入先__TOTAL__件（地図マーカー__MARKER_COUNT__件 / オンライン__ONLINE_COUNT__件）。オンライン仕入先は一覧・詳細のみ表示します。</p>
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
const suppliers = __SUPPLIERS_JSON__;
const categoryLabels = __CATEGORY_LABELS_JSON__;

let currentCategory = "all";
let selectedUid = null;
let markers = new Map();
let lastInteractionSource = null;

const supplierByUid = new Map(
  suppliers.map(s => [String(s._uid || "").trim(), s])
);

const map = L.map("map").setView([34.34, 134.05], 11);

L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap &copy; CARTO"
}).addTo(map);

function esc(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function label(cat) {
  return categoryLabels[cat] || cat || "";
}

function isOnline(s) {
  const value = String(s.local_or_online || "").toLowerCase();
  return value.includes("オンライン") || value === "online";
}

function hasCoordinate(s) {
  if (s.latitude === null || s.longitude === null) return false;
  if (s.latitude === undefined || s.longitude === undefined) return false;
  if (String(s.latitude).trim() === "" || String(s.longitude).trim() === "") return false;

  const lat = Number(s.latitude);
  const lng = Number(s.longitude);

  return Number.isFinite(lat) && Number.isFinite(lng);
}

function addressText(s) {
  return isOnline(s) ? "オンライン" : (s.address_candidate || "");
}

function textOf(s) {
  return Object.values(s).join(" ").toLowerCase();
}

function filteredSuppliers() {
  const q = document.getElementById("searchBox").value.toLowerCase().trim();

  return suppliers.filter(s => {
    const catOk = currentCategory === "all" || s.source_category === currentCategory;
    const qOk = !q || textOf(s).includes(q);
    return catOk && qOk;
  });
}

function popupHtml(s) {
  return `
    <strong>${esc(s.name)}</strong><br>
    <span>${esc(label(s.source_category))} / ${esc(s.type || "")}</span><br>
    <span>${esc(addressText(s))}</span>
  `;
}

function cardHtml(s) {
  const uid = esc(String(s._uid || "").trim());
  const onlineClass = isOnline(s) ? " online" : "";

  return `
    <div class="item ${String(s._uid).trim() === selectedUid ? "active" : ""}"
         id="card-${uid}"
         data-supplier-uid="${uid}">
      <div class="item-title">${esc(s.name)}</div>

      <div>
        <span class="badge">${esc(label(s.source_category))}</span>
        <span class="badge">${esc(s.type || "")}</span>
        <span class="badge${onlineClass}">${esc(isOnline(s) ? "オンライン" : (s.local_or_online || "ローカル"))}</span>
      </div>

      <div class="items">${esc(s.main_items || "")}</div>
      <div class="notes">${esc(s.notes || "")}</div>

      <div class="links">
        ${s.official_url ? `<a href="${esc(s.official_url)}" target="_blank" rel="noopener">公式サイト</a>` : ""}
        ${(!isOnline(s) && s.google_maps_url) ? ` / <a href="${esc(s.google_maps_url)}" target="_blank" rel="noopener">Google Maps</a>` : ""}
      </div>

      <div class="addr">${esc(addressText(s))}</div>
    </div>
  `;
}

function renderMarkers(list, fitMap = true) {
  markers.forEach(marker => map.removeLayer(marker));
  markers.clear();

  const bounds = [];

  list.forEach(s => {
    const uid = String(s._uid || "").trim();

    if (!uid || isOnline(s) || !hasCoordinate(s)) return;

    const lat = Number(s.latitude);
    const lng = Number(s.longitude);
    const marker = L.marker([lat, lng]).addTo(map).bindPopup(popupHtml(s));

    marker.on("click", () => {
      selectSupplier(uid, {
        source: "marker",
        moveMap: false,
        scrollList: true,
        openPopup: false
      });
    });

    markers.set(uid, marker);
    bounds.push([lat, lng]);
  });

  if (fitMap && bounds.length) {
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 13 });
  }
}

function renderList(list) {
  const markerCount = list.filter(s => !isOnline(s) && hasCoordinate(s)).length;
  const onlineCount = list.filter(isOnline).length;

  document.getElementById("summary").textContent =
    `${list.length}件表示 / 全${suppliers.length}件（地図${markerCount}件・オンライン${onlineCount}件）`;

  const listEl = document.getElementById("supplierList");

  listEl.innerHTML =
    list.map(cardHtml).join("") || `<div class="empty">該当する仕入先がありません。</div>`;
}

function renderDetail(s) {
  const detailEl = document.getElementById("detail");

  if (!s) {
    detailEl.innerHTML =
      `<div class="empty">左の一覧または地図上のピンから仕入先を選択してください。</div>`;
    return;
  }

  detailEl.innerHTML = `
    <h2>${esc(s.name)}</h2>
    <div class="detail-grid">
      <div class="label">カテゴリ</div><div>${esc(label(s.source_category))}</div>
      <div class="label">分類</div><div>${esc(s.type || "")}</div>
      <div class="label">取引形態</div><div>${esc(isOnline(s) ? "オンライン" : (s.local_or_online || "ローカル"))}</div>
      <div class="label">住所</div><div>${esc(addressText(s))}</div>
      <div class="label">取扱</div><div>${esc(s.main_items || "")}</div>
      <div class="label">メモ</div><div>${esc(s.notes || "")}</div>
      <div class="label">公式</div>
      <div>${s.official_url ? `<a href="${esc(s.official_url)}" target="_blank" rel="noopener">公式サイト</a>` : ""}</div>
      <div class="label">Google</div>
      <div>${(!isOnline(s) && s.google_maps_url) ? `<a href="${esc(s.google_maps_url)}" target="_blank" rel="noopener">Google Maps</a>` : ""}</div>
    </div>
  `;
}

function updateActiveCard(uid) {
  document.querySelectorAll(".item").forEach(card => {
    card.classList.toggle(
      "active",
      String(card.dataset.supplierUid || "").trim() === uid
    );
  });
}

function scrollToCard(uid) {
  const listEl = document.getElementById("supplierList");
  const card = document.getElementById(`card-${uid}`);

  if (!listEl || !card) return;

  const listRect = listEl.getBoundingClientRect();
  const cardRect = card.getBoundingClientRect();

  const targetTop =
    listEl.scrollTop +
    (cardRect.top - listRect.top) -
    (listEl.clientHeight / 2) +
    (card.offsetHeight / 2);

  listEl.scrollTo({
    top: Math.max(0, targetTop),
    behavior: "smooth"
  });
}

function selectSupplier(uid, options = {}) {
  const normalizedUid = String(uid || "").trim();

  if (!normalizedUid) {
    console.warn("empty supplier uid");
    return;
  }

  selectedUid = normalizedUid;
  lastInteractionSource = options.source || "list";

  const moveMap = options.moveMap ?? false;
  const scrollList = options.scrollList ?? false;
  const openPopup = options.openPopup ?? true;

  const s = supplierByUid.get(normalizedUid);

  if (!s) {
    console.warn("supplier not found:", normalizedUid);
    return;
  }

  renderDetail(s);
  updateActiveCard(normalizedUid);

  if (scrollList) {
    scrollToCard(normalizedUid);
  }

  const marker = markers.get(normalizedUid);

  if (marker) {
    if (moveMap) {
      map.setView(marker.getLatLng(), 15, { animate: false });
    }

    if (openPopup) {
      marker.openPopup();
    }
  }
}

function renderAll(fitMap = true) {
  selectedUid = null;

  const list = filteredSuppliers();

  renderList(list);
  renderMarkers(list, fitMap);
  renderDetail(null);
}

document.getElementById("supplierList").addEventListener("click", (e) => {
  if (e.target.closest("a")) return;

  const card = e.target.closest(".item");
  if (!card) return;

  const uid = String(card.dataset.supplierUid || "").trim();
  if (!uid) return;

  selectSupplier(uid, {
    source: "list",
    moveMap: true,
    scrollList: false,
    openPopup: true
  });
});

document.querySelectorAll(".filter").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentCategory = btn.dataset.category;
    renderAll(true);
  });
});

document.getElementById("searchBox").addEventListener("input", () => {
  renderAll(true);
});

renderAll(true);
</script>
</body>
</html>
"""


def build_html(records: list[dict], stats: dict) -> str:
    html = HTML_TEMPLATE
    html = html.replace("__SUPPLIERS_JSON__", json.dumps(records, ensure_ascii=False))
    html = html.replace("__CATEGORY_LABELS_JSON__", json.dumps(CATEGORY_LABELS, ensure_ascii=False))
    html = html.replace("__TOTAL__", str(stats["total"]))
    html = html.replace("__MARKER_COUNT__", str(stats["marker_count"]))
    html = html.replace("__ONLINE_COUNT__", str(stats["online_count"]))
    return html


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    records, stats = build_supplier_records()
    html = build_html(records, stats)

    OUT_PATH.write_text(html, encoding="utf-8")

    print(f"[SAVE] {OUT_PATH}")
    print("[ROWS]", stats["total"])
    print("[LOCAL]", stats["local_count"])
    print("[ONLINE]", stats["online_count"])
    print("[MARKERS]", stats["marker_count"])


if __name__ == "__main__":
    main()
