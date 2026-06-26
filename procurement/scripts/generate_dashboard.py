from pathlib import Path
import json
import math
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
MASTER_DIR = BASE_DIR / "output" / "master"
OUT_DIR = BASE_DIR / "output" / "dashboard"
OUT_PATH = OUT_DIR / "procurement_dashboard.html"

CATEGORY_LABELS = {
    "all": "すべて",
    "fruit": "フルーツ",
    "coffee": "コーヒー",
    "consumables": "消耗品",
    "materials": "原材料",
    "ice": "氷",
}

SUPPLIER_COLUMNS = [
    "supplier_id", "name", "type", "local_or_online", "official_url", "google_maps_url",
    "main_items", "delivery_available", "pickup_available", "notes", 
    "product_tags","fruit_tags","coffee_tags","dairy_tags","tea_tags",
    "syrup_tags","powder_tags","cup_tags","container_tags","packaging_tags",
    "machine_tags","ice_tags","other_tags","strength_tags",
    "order_methods","minimum_order","minimum_amount","delivery_area","delivery_days",
    "payment_methods","business_hours","closed_days","target_customers","last_verified",
    "source_url","info_confidence","research_status","notes_research","source_category",
]

PRICE_COLUMNS = [
    "category", "item_name", "unit", "observation_count", "median_unit_price_yen",
    "mean_unit_price_yen", "min_unit_price_yen", "max_unit_price_yen",
    "suppliers", "source_urls", "latest_checked_date",
]

FRUIT_PRICE_COLUMNS = [
    "item_name", "product_form", "unit", "observation_count", "median_unit_price_yen",
    "mean_unit_price_yen", "min_unit_price_yen", "max_unit_price_yen",
    "suppliers", "source_urls", "latest_checked_date",
]


def normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def load_csv(name: str, columns: list[str]) -> list[dict]:
    path = MASTER_DIR / name
    if not path.exists():
        print(f"[WARN] missing: {path}")
        return []

    df = pd.read_csv(path, encoding="utf-8-sig").fillna("")
    df = ensure_columns(df, columns)

    # JSONにNaNを混ぜない。数値列は数値、それ以外は文字列に正規化。
    records: list[dict] = []
    numeric_cols = {
        "observation_count",
        "median_unit_price_yen",
        "mean_unit_price_yen",
        "min_unit_price_yen",
        "max_unit_price_yen",
    }

    for _, row in df.iterrows():
        record = {}
        for col in columns:
            value = row.get(col, "")
            if col in numeric_cols:
                num = pd.to_numeric(value, errors="coerce")
                record[col] = float(num) if pd.notna(num) else None
            else:
                record[col] = normalize_text(value)
        records.append(record)

    return records


def build_stats(suppliers: list[dict], prices: list[dict], fruit_prices: list[dict]) -> dict:
    local_count = sum(1 for s in suppliers if "オンライン" not in normalize_text(s.get("local_or_online")))
    online_count = len(suppliers) - local_count
    return {
        "supplier_total": len(suppliers),
        "local_count": local_count,
        "online_count": online_count,
        "price_total": len(prices),
        "fruit_price_total": len(fruit_prices),
    }


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>カフェ仕入れ調査ダッシュボード</title>
<style>
:root {
  --brown:#2f241d;
  --paper:#f6f4ef;
  --cream:#f3eee7;
  --line:#e8e1d8;
  --muted:#666;
  --blue:#0b63ce;
  --green:#356b2d;
}
* { box-sizing:border-box; }
html { min-height:100%; }
body { margin:0; min-height:100%; font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--paper); color:#222; overflow:auto; }
a { color:#0645ad; text-decoration:none; }
a:hover { text-decoration:underline; }
header { background:var(--brown); color:white; padding:16px 24px; }
header h1 { margin:0; font-size:24px; }
header p { margin:5px 0 0; color:#ddd; font-size:13px; }
.layout { display:grid; grid-template-columns:300px minmax(0,1fr); gap:18px; padding:18px; min-height:calc(100vh - 72px); align-items:start; overflow:visible; }
main { min-width:0; min-height:0; overflow:visible; display:flex; flex-direction:column; }
.sidebar,.panel { background:white; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,.08); padding:16px; }
.size-controls { display:flex; gap:6px; flex-wrap:wrap; align-items:center; justify-content:flex-end; margin:4px 0 8px; }
.size-btn { width:auto; margin:0; padding:4px 8px; border:1px solid #ddd; border-radius:999px; background:#fafafa; cursor:pointer; font-size:12px; line-height:1.2; }
.size-btn:hover { background:#f7f1e9; }
.size-btn.active { background:var(--brown); color:white; }
.panel-hint { color:#888; font-size:11px; margin-right:auto; }
.resize-grip { height:8px; margin:8px 18px -6px 0; border-radius:999px; background:linear-gradient(90deg, transparent, #ddd, transparent); cursor:ns-resize; flex:0 0 auto; }
.resize-grip:hover { background:linear-gradient(90deg, transparent, #bca891, transparent); }
.resize-side-grip { position:absolute; top:44px; right:0; width:10px; height:calc(100% - 56px); cursor:ew-resize; border-radius:999px; background:transparent; z-index:30; touch-action:none; }
.resize-side-grip:hover { background:linear-gradient(180deg, transparent, rgba(188,168,145,.45), transparent); }
.resize-corner-grip { position:absolute; right:2px; bottom:2px; width:18px; height:18px; cursor:nwse-resize; z-index:31; touch-action:none; }
.resize-corner-grip::after { content:""; position:absolute; right:2px; bottom:2px; width:12px; height:12px; border-right:3px solid #c8b8a6; border-bottom:3px solid #c8b8a6; border-radius:2px; }
.resize-corner-grip:hover::after { border-color:#8f765f; }
.sidebar { position:sticky; top:18px; max-height:none; }
.sidebar.scroll-panel { height:var(--panel-h, calc(100vh - 108px)); min-height:320px; max-height:none; }
.sidebar h2 { font-size:16px; margin:0 0 8px; }
.sidebar-section { border-top:1px solid var(--line); padding-top:12px; margin-top:12px; }
.btn { width:100%; margin:5px 0; padding:9px 10px; border:1px solid #ddd; border-radius:10px; background:#fafafa; cursor:pointer; text-align:left; font-size:14px; }
.btn:hover { background:#f7f1e9; }
.btn.active { background:var(--brown); color:white; }
.sub-btn { padding-left:22px; font-size:13px; }
input, select { width:100%; padding:10px; border:1px solid #ddd; border-radius:10px; margin:8px 0; background:white; }
.main-grid { min-height:720px; display:grid; grid-template-columns:minmax(0,1fr) 410px; gap:18px; align-items:start; overflow:visible; }
.center-col { min-width:0; min-height:0; display:flex; flex-direction:column; gap:18px; overflow:visible; }
.right-col { min-width:0; min-height:0; display:flex; flex-direction:column; gap:18px; overflow:visible; }
.panel { margin-bottom:18px; }
.panel.drag-enabled .panel-head { cursor:grab; user-select:none; }
.panel.drag-enabled .panel-head:active { cursor:grabbing; }
.panel.drag-enabled .size-controls, .panel.drag-enabled .count, .panel.drag-enabled button, .panel.drag-enabled a, .panel.drag-enabled input, .panel.drag-enabled select { cursor:auto; }
.panel.dragging { opacity:.45; outline:2px dashed #bca891; }
.drag-over-zone { outline:2px dashed #d7c2a6; outline-offset:4px; border-radius:16px; min-height:120px; }
.layout-tools { display:flex; justify-content:flex-end; align-items:center; gap:8px; margin:-8px 0 14px; }
.layout-tools .mini-btn { background:white; }
.scroll-panel { display:flex; flex-direction:column; min-height:220px; height:var(--panel-h, 360px); overflow:hidden; margin-bottom:0; position:relative; }
.scroll-panel.compact { height:260px; }
.scroll-panel.medium { height:380px; }
.scroll-panel.large { height:560px; }
.scroll-panel.full { height:calc(100vh - 140px); }
.panel-body { flex:1; min-height:0; overflow:auto; padding-right:4px; }
.panel-head { flex:0 0 auto; }
.panel h2 { margin:0 0 8px; font-size:20px; }
.panel h3 { margin:0 0 8px; }
.stats { display:grid; grid-template-columns:repeat(5,minmax(110px,1fr)); gap:10px; margin-bottom:18px; }
.stat { background:white; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,.08); padding:13px; }
.stat .num { font-size:24px; font-weight:800; }
.stat .label { color:var(--muted); font-size:12px; }
.count { font-size:13px; color:var(--muted); margin-bottom:10px; }
.card { border:1px solid #eee; border-radius:14px; padding:14px; margin-bottom:10px; background:white; transition:.15s; }
.card:hover { border-color:#d9c8b7; box-shadow:0 2px 8px rgba(47,36,29,.10); }
.card.active { border-color:var(--brown); background:#fbf7f1; box-shadow:0 2px 10px rgba(47,36,29,.18); }
.card-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.card-title { margin:0 0 6px; font-size:18px; }
.badge { display:inline-block; background:#eee2d2; border-radius:999px; padding:3px 8px; font-size:12px; margin:0 4px 4px 0; }
.badge.online { background:#dde7f7; }
.badge.local { background:#e1edd8; }
.badge.price { background:#e8e6f7; }
.card-body { line-height:1.55; font-size:14px; }
.meta-grid { display:grid; grid-template-columns:92px 1fr; gap:6px 10px; font-size:14px; margin-top:10px; }
.meta-label { color:#777; }
.detail-section { border:1px solid #eee; border-radius:14px; padding:12px; margin-top:12px; background:#fff; }
.detail-section-title { font-weight:800; color:#2f241d; margin-bottom:8px; font-size:14px; }
.detail-section .meta-grid { margin-top:0; }
.actions { margin-top:10px; display:flex; gap:8px; flex-wrap:wrap; }
.small-link, .mini-btn { display:inline-block; border:1px solid #ddd; border-radius:999px; padding:5px 10px; background:#fafafa; font-size:12px; cursor:pointer; }
.mini-btn.active { background:var(--brown); color:white; }
.compare-check { transform:scale(1.1); width:auto; margin:0 6px 0 0; }
.detail-empty { color:#777; padding:20px; text-align:center; }
#supplierPanel { --panel-h:520px; }
#pricePanel { --panel-h:390px; }
#detailPanel { --panel-h:430px; }
#relatedPanel { --panel-h:330px; }
#comparePanel { --panel-h:330px; }
.detail-title { font-size:22px; margin:0 0 8px; }
.mapbox { width:100%; height:240px; border:1px solid #eee; border-radius:12px; overflow:hidden; background:#f7f7f7; margin-top:10px; }
.mapbox iframe { width:100%; height:100%; border:0; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th,td { border-bottom:1px solid #eee; padding:8px; text-align:left; vertical-align:top; }
th { background:var(--cream); position:sticky; top:0; z-index:1; }
.table-wrap { overflow:auto; max-height:440px; border:1px solid #eee; border-radius:12px; }
/* テーブルカードは、カード本体だけで縦横スクロールできるようにする。 */
.panel-body > .table-wrap {
  max-height:none;
  min-height:0;
  height:100%;
  overflow:auto;
}
#priceTableBody,
#fruitPriceTableBody {
  overflow:auto;
}
#priceTableBody > .table-wrap,
#fruitPriceTableBody > .table-wrap {
  overflow:auto;
}
#priceTableBody table,
#fruitPriceTableBody table {
  min-width:980px;
}
tr.clickable { cursor:pointer; }
tr.clickable:hover { background:#fbf7f1; }
.price-selected { outline:2px solid #d0b48e; background:#fbf7f1; }
.notice { background:#fff8df; border:1px solid #f0dfa9; border-radius:12px; padding:10px; font-size:13px; margin:8px 0; color:#5b481a; }
.compare-table th:first-child { width:110px; }
.compare-table td, .compare-table th { min-width:150px; }
.empty { color:#777; padding:12px; }

/* free-placement dashboard layer */
.layout.free-layout {
  display:block;
  position:relative;
  min-height:1800px;
  padding:18px;
  overflow:visible;
}
.free-layout main,
.free-layout .main-grid,
.free-layout .center-col,
.free-layout .right-col {
  display:block;
  position:static;
  overflow:visible;
  min-height:0;
}
.free-layout .stats {
  position:absolute;
  left:336px;
  top:18px;
  width:calc(100% - 354px);
  z-index:1;
}
.free-layout .layout-tools {
  position:absolute;
  left:336px;
  top:108px;
  width:calc(100% - 354px);
  z-index:5;
}
.free-layout .scroll-panel[data-dashboard-panel] {
  position:absolute;
  left:var(--panel-x, 18px);
  top:var(--panel-y, 18px);
  width:var(--panel-w, 420px);
  z-index:var(--panel-z, 10);
  margin:0;
  max-width:none;
}
.free-layout #filterPanel { --panel-x:18px; --panel-y:18px; --panel-w:300px; }
.free-layout #supplierPanel { --panel-x:336px; --panel-y:154px; --panel-w:620px; }
.free-layout #pricePanel { --panel-x:336px; --panel-y:692px; --panel-w:620px; }
.free-layout #detailPanel { --panel-x:974px; --panel-y:154px; --panel-w:430px; }
.free-layout #relatedPanel { --panel-x:974px; --panel-y:602px; --panel-w:430px; }
.free-layout #comparePanel { --panel-x:974px; --panel-y:950px; --panel-w:430px; }
.free-layout .panel.drag-enabled .panel-head,
.free-layout .sidebar.drag-enabled .panel-head {
  cursor:grab;
  touch-action:none;
  user-select:none;
}
.free-layout .panel.drag-enabled .panel-head:active,
.free-layout .sidebar.drag-enabled .panel-head:active { cursor:grabbing; }
.free-layout .panel.free-dragging,
.free-layout .sidebar.free-dragging {
  opacity:.92;
  outline:2px solid #bca891;
  box-shadow:0 16px 36px rgba(47,36,29,.22);
}
.free-layout .free-layout-help {
  position:absolute;
  right:18px;
  top:18px;
  font-size:12px;
  color:#666;
}

@media (max-width: 1100px) {
  .layout { grid-template-columns:1fr; }
  body { overflow:auto; }
  .layout { height:auto; overflow:visible; grid-template-columns:1fr; }
  main, .main-grid, .center-col, .right-col { overflow:visible; display:block; }
  .sidebar,.right-col { position:static; max-height:none; }
  .scroll-panel { display:block; margin-bottom:18px; }
  .panel-body { max-height:none; overflow:visible; }
  .main-grid { grid-template-columns:1fr; }
  .stats { grid-template-columns:repeat(2,1fr); }
}
</style>
</head>
<body>
<header>
  <h1>カフェ仕入れ調査ダッシュボード</h1>
  <p>仕入先・参考価格・フルーツ価格を連動表示。カード詳細、比較、地図確認に対応。</p>
</header>

<div class="layout free-layout" id="dashboardCanvas">
  <aside class="sidebar scroll-panel drag-enabled" id="filterPanel" data-dashboard-panel="filterPanel">
    <div class="panel-head">
      <h2>絞り込み</h2>
      <div class="size-controls" data-panel-controls="filterPanel">
        <span class="panel-hint">高さ調整</span>
        <button class="size-btn" data-size="compact">小</button>
        <button class="size-btn active" data-size="medium">中</button>
        <button class="size-btn" data-size="large">大</button>
        <button class="size-btn" data-size="full">最大</button>
        <button class="size-btn" data-size="reset">リセット</button>
      </div>
      <input id="searchBox" placeholder="名称・取扱・特徴・メモで検索">
    </div>

    <div class="panel-body" id="filterPanelBody">
    <div class="sidebar-section">
      <strong>カテゴリ</strong>
      <button class="btn filter active" data-category="all">すべて</button>
      <button class="btn filter" data-category="fruit">フルーツ</button>
      <button class="btn filter" data-category="coffee">コーヒー</button>
      <button class="btn filter" data-category="consumables">消耗品</button>
      <button class="btn filter" data-category="materials">原材料</button>
      <button class="btn filter" data-category="ice">氷</button>
    </div>

    <div class="sidebar-section">
      <strong>ローカル / オンライン</strong>
      <button class="btn scope active" data-scope="all">すべて</button>
      <button class="btn scope" data-scope="local">ローカルのみ</button>
      <button class="btn scope" data-scope="online">オンラインのみ</button>
    </div>

    <div class="sidebar-section">
      <strong>詳細タグ</strong>
      <button class="btn item-filter active" data-item="">指定なし</button>
      <button class="btn item-filter sub-btn" data-item="冷凍 フルーツ ピューレ ダイス">フルーツ：冷凍・ピューレ</button>
      <button class="btn item-filter sub-btn" data-item="生鮮 果物 青果 産直">フルーツ：生鮮・産直</button>
      <button class="btn item-filter sub-btn" data-item="シロップ ソース フラッペ MONIN Torani DaVinci">ドリンク：シロップ・ソース</button>
      <button class="btn item-filter sub-btn" data-item="コーヒー 豆 ブレンド スペシャルティ ロースター">コーヒー：豆・ロースター</button>
      <button class="btn item-filter sub-btn" data-item="紙カップ PETカップ ストロー おしぼり 包材 容器">消耗品：包材・カップ</button>
      <button class="btn item-filter sub-btn" data-item="牛乳 生クリーム ヨーグルト 抹茶 はちみつ">原材料：乳製品・抹茶等</button>
      <button class="btn item-filter sub-btn" data-item="氷 ロックアイス 製氷機 ドライアイス">氷：氷・製氷機</button>
    </div>

    <div class="sidebar-section">
      <strong>並び替え</strong>
      <select id="sortSelect">
        <option value="id">ID順</option>
        <option value="name">名称順</option>
        <option value="category">カテゴリ順</option>
        <option value="type">分類順</option>
      </select>
    </div>

    <div class="sidebar-section">
      <button class="btn" id="clearAllBtn">絞り込み解除</button>
    </div>
    </div>
    <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="filterPanel" title="ドラッグで幅調整"></div>

    <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="filterPanel" title="ドラッグで幅と高さを同時調整"></div>

    <div class="resize-grip" data-resize-panel="filterPanel" title="ドラッグで高さ調整"></div>
  </aside>

  <main>
    <div class="stats">
      <div class="stat"><div class="num">__SUPPLIER_TOTAL__</div><div class="label">仕入先</div></div>
      <div class="stat"><div class="num">__LOCAL_COUNT__</div><div class="label">ローカル</div></div>
      <div class="stat"><div class="num">__ONLINE_COUNT__</div><div class="label">オンライン</div></div>
      <div class="stat"><div class="num">__PRICE_TOTAL__</div><div class="label">参考価格</div></div>
    </div>

    <div class="layout-tools">
      <span class="panel-hint">カード見出しをドラッグして、画面上に自由配置できます。</span>
      <button class="mini-btn" id="resetLayoutBtn" type="button">配置リセット</button>
    </div>

    <div class="main-grid">
      <div class="center-col">
        <section class="panel scroll-panel drag-enabled" id="supplierPanel" data-dashboard-panel="supplierPanel">
          <div class="panel-head">
            <h2 id="supplierTitle">仕入先一覧</h2>
            <div class="size-controls" data-panel-controls="supplierPanel">
              <span class="panel-hint">高さ調整</span>
              <button class="size-btn" data-size="compact">小</button>
              <button class="size-btn active" data-size="medium">中</button>
              <button class="size-btn" data-size="large">大</button>
              <button class="size-btn" data-size="full">最大</button>
              <button class="size-btn" data-size="reset">リセット</button>
            </div>
            <div class="count" id="supplierCount"></div>
            <div id="activeFilterNotice"></div>
          </div>
          <div class="panel-body" id="supplierListBody">
            <div id="supplierList"></div>
          </div>
          <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="supplierPanel" title="ドラッグで幅調整"></div>

          <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="supplierPanel" title="ドラッグで幅と高さを同時調整"></div>

          <div class="resize-grip" data-resize-panel="supplierPanel" title="ドラッグで高さ調整"></div>
        </section>

        <section class="panel scroll-panel drag-enabled" id="pricePanel" data-dashboard-panel="pricePanel">
          <div class="panel-head">
            <h2 id="priceTitle">参考価格マスター</h2>
            <div class="size-controls" data-panel-controls="pricePanel">
              <span class="panel-hint">高さ調整</span>
              <button class="size-btn" data-size="compact">小</button>
              <button class="size-btn active" data-size="medium">中</button>
              <button class="size-btn" data-size="large">大</button>
              <button class="size-btn" data-size="full">最大</button>
              <button class="size-btn" data-size="reset">リセット</button>
            </div>
            <div class="count" id="priceCount"></div>
          </div>
          <div class="panel-body" id="priceTableBody">
            <div class="table-wrap" id="priceTable"></div>
          </div>
          <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="pricePanel" title="ドラッグで幅調整"></div>

          <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="pricePanel" title="ドラッグで幅と高さを同時調整"></div>

          <div class="resize-grip" data-resize-panel="pricePanel" title="ドラッグで高さ調整"></div>
        </section>

      </div>

      <div class="right-col">
        <section class="panel scroll-panel drag-enabled" id="detailPanel" data-dashboard-panel="detailPanel">
          <div class="panel-head">
            <h2>仕入先詳細</h2>
            <div class="size-controls" data-panel-controls="detailPanel">
              <span class="panel-hint">高さ調整</span>
              <button class="size-btn" data-size="compact">小</button>
              <button class="size-btn active" data-size="medium">中</button>
              <button class="size-btn" data-size="large">大</button>
              <button class="size-btn" data-size="full">最大</button>
              <button class="size-btn" data-size="reset">リセット</button>
            </div>
          </div>
          <div class="panel-body" id="detailBody">
            <div id="supplierDetail"><div class="detail-empty">仕入先カードをクリックすると詳細を表示します。</div></div>
          </div>
          <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="detailPanel" title="ドラッグで幅調整"></div>

          <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="detailPanel" title="ドラッグで幅と高さを同時調整"></div>

          <div class="resize-grip" data-resize-panel="detailPanel" title="ドラッグで高さ調整"></div>
        </section>

        <section class="panel scroll-panel drag-enabled" id="relatedPanel" data-dashboard-panel="relatedPanel">
          <div class="panel-head">
            <h2>関連価格</h2>
            <div class="size-controls" data-panel-controls="relatedPanel">
              <span class="panel-hint">高さ調整</span>
              <button class="size-btn" data-size="compact">小</button>
              <button class="size-btn active" data-size="medium">中</button>
              <button class="size-btn" data-size="large">大</button>
              <button class="size-btn" data-size="full">最大</button>
              <button class="size-btn" data-size="reset">リセット</button>
            </div>
          </div>
          <div class="panel-body" id="relatedBody">
            <div id="relatedPrices"><div class="empty">仕入先または価格行を選択してください。</div></div>
          </div>
          <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="relatedPanel" title="ドラッグで幅調整"></div>

          <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="relatedPanel" title="ドラッグで幅と高さを同時調整"></div>

          <div class="resize-grip" data-resize-panel="relatedPanel" title="ドラッグで高さ調整"></div>
        </section>

        <section class="panel scroll-panel drag-enabled" id="comparePanel" data-dashboard-panel="comparePanel">
          <div class="panel-head">
            <h2>比較</h2>
            <div class="size-controls" data-panel-controls="comparePanel">
              <span class="panel-hint">高さ調整</span>
              <button class="size-btn" data-size="compact">小</button>
              <button class="size-btn active" data-size="medium">中</button>
              <button class="size-btn" data-size="large">大</button>
              <button class="size-btn" data-size="full">最大</button>
              <button class="size-btn" data-size="reset">リセット</button>
            </div>
            <div class="count" id="compareCount"></div>
          </div>
          <div class="panel-body" id="compareBody">
            <div id="compareTable"><div class="empty">比較したい仕入先にチェックを入れてください。</div></div>
          </div>
          <div class="resize-side-grip" data-resize-dir="width" data-resize-panel="comparePanel" title="ドラッグで幅調整"></div>

          <div class="resize-corner-grip" data-resize-dir="both" data-resize-panel="comparePanel" title="ドラッグで幅と高さを同時調整"></div>

          <div class="resize-grip" data-resize-panel="comparePanel" title="ドラッグで高さ調整"></div>
        </section>
      </div>
    </div>
  </main>
</div>

<script>
const suppliers = __SUPPLIERS_JSON__;
const prices = __PRICES_JSON__;
const fruitPrices = __FRUIT_PRICES_JSON__;
const allPrices = [
  ...prices.map(p => ({...p, _kind:"general"})),
  ...fruitPrices.map(p => ({...p, category:"fruit", _kind:"fruit"})),
];
const categoryLabels = __CATEGORY_LABELS_JSON__;

let currentCategory = "all";
let currentScope = "all";
let itemKeyword = "";
let selectedSupplierId = null;
let selectedPriceKey = null;
let compareIds = new Set();

const supplierById = new Map(suppliers.map(s => [String(s.supplier_id || "").trim(), s]));

function esc(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
function label(cat) { return categoryLabels[cat] || cat || ""; }
function clean(v) { return String(v ?? "").trim(); }
function dash(v) {
  const text = clean(v);
  if (!text || text.toLowerCase() === "nan") return "---";
  return text;
}
function joinNonEmpty(values) {
  const list = values.map(v => dash(v)).filter(v => v !== "---");
  return list.length ? list.join(" / ") : "---";
}
function lowerText(v) { return clean(v).toLowerCase(); }
function isOnline(s) { return lowerText(s.local_or_online).includes("オンライン") || lowerText(s.local_or_online) === "online"; }
function supplierCategory(s) { return clean(s.source_category); }
function priceCategory(p) { return clean(p.category || "fruit"); }
function matchesCategory(cat, target) { return target === "all" || cat === target; }
function yen(v, digits = 2) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "";
  return n.toLocaleString("ja-JP", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}
function supplierSearchText(s) { return Object.values(s).join(" ").toLowerCase(); }
function priceSearchText(p) { return Object.values(p).join(" ").toLowerCase(); }
function keywordTokens(text) { return lowerText(text).split(/[\s　・/／,、]+/).map(t => t.trim()).filter(Boolean); }
function supplierMatchesKeyword(s, keyword) {
  if (!keyword) return true;
  const text = supplierSearchText(s);
  const tokens = keywordTokens(keyword);
  return tokens.some(t => text.includes(t));
}
function sourceLinks(names, urls) {
  if (!names) return "";
  const nameList = String(names).split(" / ");
  const urlList = urls ? String(urls).split(" / ") : [];
  return nameList.map((name, i) => {
    const safeName = esc(name);
    const url = clean(urlList[i]);
    return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${safeName}</a>` : safeName;
  }).join(" / ");
}
function priceKey(p, prefix) {
  return `${prefix}:${clean(p.category || "fruit")}:${clean(p.item_name)}:${clean(p.product_form)}:${clean(p.unit)}`;
}
function priceKeyword(p) {
  return [p.item_name, p.product_form, p.unit, p.suppliers, p.category].filter(Boolean).join(" ");
}
function relatedPricesForSupplier(s) {
  if (!s) return [];
  const cat = supplierCategory(s);
  const text = supplierSearchText(s);
  let related = allPrices.filter(p => priceCategory(p) === cat && keywordTokens(priceKeyword(p)).some(t => text.includes(t)));
  if (!related.length) related = allPrices.filter(p => priceCategory(p) === cat);
  return related;
}
function suppliersForPrice(p) {
  const cat = priceCategory(p);
  const tokens = keywordTokens(priceKeyword(p)).filter(t => !["kg","g","ml","本","個","枚","換算","冷凍","生鮮"].includes(t));
  let matched = suppliers.filter(s => supplierCategory(s) === cat && tokens.some(t => supplierSearchText(s).includes(t)));
  if (!matched.length) matched = suppliers.filter(s => supplierCategory(s) === cat);
  return matched;
}
function setActiveButtons(selector, attr, value) {
  document.querySelectorAll(selector).forEach(btn => btn.classList.toggle("active", clean(btn.dataset[attr]) === value));
}
function updateUrlSupplier(id) {
  const url = new URL(window.location.href);
  if (id) url.searchParams.set("supplier_id", id);
  else url.searchParams.delete("supplier_id");
  history.replaceState(null, "", url.toString());
}
function scrollPanelBodyToTop(id) {
  const el = document.getElementById(id);
  if (el) el.scrollTo({ top: 0, behavior: "smooth" });
}
function syncCompareCheckboxes() {
  document.querySelectorAll(".compare-check").forEach(cb => {
    cb.checked = compareIds.has(clean(cb.dataset.compareId));
  });
}

function filteredSuppliers() {
  const q = lowerText(document.getElementById("searchBox").value);
  let list = suppliers.filter(s => {
    const catOk = matchesCategory(supplierCategory(s), currentCategory);
    const scopeOk = currentScope === "all" || (currentScope === "online" ? isOnline(s) : !isOnline(s));
    const textOk = !q || supplierSearchText(s).includes(q);
    const itemOk = supplierMatchesKeyword(s, itemKeyword);
    return catOk && scopeOk && textOk && itemOk;
  });

  const sort = document.getElementById("sortSelect").value;
  list.sort((a, b) => {
    if (sort === "name") return clean(a.name).localeCompare(clean(b.name), "ja");
    if (sort === "category") return clean(a.source_category).localeCompare(clean(b.source_category), "ja") || clean(a.supplier_id).localeCompare(clean(b.supplier_id));
    if (sort === "type") return clean(a.type).localeCompare(clean(b.type), "ja") || clean(a.name).localeCompare(clean(b.name), "ja");
    return clean(a.supplier_id).localeCompare(clean(b.supplier_id), "ja");
  });
  return list;
}

function renderActiveFilterNotice() {
  const parts = [];
  if (currentCategory !== "all") parts.push(`カテゴリ：${label(currentCategory)}`);
  if (currentScope !== "all") parts.push(currentScope === "online" ? "オンラインのみ" : "ローカルのみ");
  if (itemKeyword) parts.push(`詳細タグ：${esc(itemKeyword)}`);
  if (selectedPriceKey) parts.push("価格行から関連候補を表示中");
  document.getElementById("activeFilterNotice").innerHTML = parts.length ? `<div class="notice">${parts.join(" / ")}</div>` : "";
}

function renderSuppliers(customList = null) {
  const list = customList || filteredSuppliers();
  const localCount = list.filter(s => !isOnline(s)).length;
  const onlineCount = list.length - localCount;
  document.getElementById("supplierTitle").textContent = `仕入先一覧：${label(currentCategory)}`;
  document.getElementById("supplierCount").textContent = `${list.length}件 / 全${suppliers.length}件（ローカル${localCount}件・オンライン${onlineCount}件）`;
  renderActiveFilterNotice();

  document.getElementById("supplierList").innerHTML = list.map(s => supplierCardHtml(s)).join("") || `<div class="empty">該当する仕入先がありません。</div>`;
}

function supplierCardHtml(s) {
  const id = esc(clean(s.supplier_id));
  const active = selectedSupplierId === clean(s.supplier_id) ? " active" : "";
  const online = isOnline(s);
  return `
    <article class="card supplier-card${active}" id="supplier-${id}" data-supplier-id="${id}">
      <div class="card-head">
        <div>
          <h3 class="card-title">${esc(s.name || "(名称なし)")}</h3>
          <div>
            <span class="badge">${esc(label(s.source_category))}</span>
            <span class="badge">${esc(s.type || "")}</span>
            <span class="badge ${online ? "online" : "local"}">${online ? "オンライン" : esc(s.local_or_online || "ローカル")}</span>
          </div>
        </div>
        <label class="small-link" title="比較に追加">
          <input class="compare-check" type="checkbox" data-compare-id="${id}" ${compareIds.has(clean(s.supplier_id)) ? "checked" : ""}>比較
        </label>
      </div>
      <div class="card-body">
        <p>${esc(dash(s.main_items))}</p>
        <p>${esc(dash(s.notes))}</p>
        <div class="meta-grid">
          <div class="meta-label">配送</div><div>${esc(dash(s.delivery_available))}</div>
          <div class="meta-label">店頭/引取</div><div>${esc(dash(s.pickup_available))}</div>
        </div>
        <div class="actions">
          <button class="mini-btn select-detail" data-supplier-id="${id}">詳細表示</button>
          ${s.official_url ? `<a class="small-link" href="${esc(s.official_url)}" target="_blank" rel="noopener">公式サイト</a>` : ""}
          ${(!online && s.google_maps_url) ? `<a class="small-link" href="${esc(s.google_maps_url)}" target="_blank" rel="noopener">Google Maps</a>` : ""}
          <a class="small-link" href="procurement_dashboard.html?supplier_id=${id}">詳細リンク</a>
        </div>
      </div>
    </article>`;
}

function renderDetail(s) {
  const el = document.getElementById("supplierDetail");
  if (!s) {
    el.innerHTML = `<div class="detail-empty">仕入先カードをクリックすると詳細を表示します。</div>`;
    return;
  }

  const online = isOnline(s);
  const mapQuery = encodeURIComponent(`${s.name || ""} ${s.google_maps_url || ""}`.trim());
  const mapHtml = online
    ? `<div class="notice">オンライン仕入先のため、地図表示は省略します。</div>`
    : `<div class="mapbox"><iframe loading="lazy" src="https://www.google.com/maps?q=${mapQuery}&output=embed"></iframe></div>`;

  const productTags = joinNonEmpty([
    s.product_tags,
    s.fruit_tags,
    s.coffee_tags,
    s.other_tags,
  ]);

  const categoryTags = joinNonEmpty([
    s.dairy_tags,
    s.tea_tags,
    s.syrup_tags,
    s.powder_tags,
    s.cup_tags,
    s.container_tags,
    s.packaging_tags,
    s.cleaning_tags,
    s.machine_tags,
    s.ice_tags,
  ]);

  el.innerHTML = `
    <h3 class="detail-title">${esc(s.name || "(名称なし)")}</h3>
    <div>
      <span class="badge">${esc(label(s.source_category))}</span>
      <span class="badge">${esc(s.type || "")}</span>
      <span class="badge ${online ? "online" : "local"}">${online ? "オンライン" : dash(s.local_or_online)}</span>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">基本情報</div>
      <div class="meta-grid">
        <div class="meta-label">ID</div><div>${dash(s.supplier_id)}</div>
        <div class="meta-label">カテゴリ</div><div>${dash(label(s.source_category))}</div>
        <div class="meta-label">分類</div><div>${dash(s.type)}</div>
        <div class="meta-label">取引形態</div><div>${online ? "オンライン" : dash(s.local_or_online)}</div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">取扱・特徴</div>
      <div class="meta-grid">
        <div class="meta-label">取扱商品</div><div>${dash(s.main_items)}</div>
        <div class="meta-label">商品タグ</div><div>${productTags}</div>
        <div class="meta-label">カテゴリタグ</div><div>${categoryTags}</div>
        <div class="meta-label">強み</div><div>${dash(s.strength_tags)}</div>
        <div class="meta-label">メモ</div><div>${dash(s.notes)}</div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">取引条件</div>
      <div class="meta-grid">
        <div class="meta-label">配送可否</div><div>${dash(s.delivery_available)}</div>
        <div class="meta-label">配送エリア</div><div>${dash(s.delivery_area)}</div>
        <div class="meta-label">配送日数</div><div>${dash(s.delivery_days)}</div>
        <div class="meta-label">店頭/引取</div><div>${dash(s.pickup_available)}</div>
        <div class="meta-label">注文方法</div><div>${dash(s.order_methods)}</div>
        <div class="meta-label">最小注文</div><div>${dash(s.minimum_order)}</div>
        <div class="meta-label">最低金額</div><div>${dash(s.minimum_amount)}</div>
        <div class="meta-label">支払方法</div><div>${dash(s.payment_methods)}</div>
        <div class="meta-label">営業時間</div><div>${dash(s.business_hours)}</div>
        <div class="meta-label">定休日</div><div>${dash(s.closed_days)}</div>
        <div class="meta-label">対象顧客</div><div>${dash(s.target_customers)}</div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">調査情報</div>
      <div class="meta-grid">
        <div class="meta-label">調査状況</div><div>${dash(s.research_status)}</div>
        <div class="meta-label">最終確認日</div><div>${dash(s.last_verified)}</div>
        <div class="meta-label">情報信頼度</div><div>${dash(s.info_confidence)}</div>
        <div class="meta-label">調査メモ</div><div>${dash(s.notes_research)}</div>
        <div class="meta-label">出典URL</div><div>${s.source_url ? `<a href="${esc(s.source_url)}" target="_blank" rel="noopener">開く</a>` : "---"}</div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">リンク</div>
      <div class="meta-grid">
        <div class="meta-label">公式</div><div>${s.official_url ? `<a href="${esc(s.official_url)}" target="_blank" rel="noopener">公式サイト</a>` : "---"}</div>
        <div class="meta-label">Google</div><div>${(!online && s.google_maps_url) ? `<a href="${esc(s.google_maps_url)}" target="_blank" rel="noopener">Google Maps</a>` : "---"}</div>
      </div>
    </div>

    ${mapHtml}
  `;
}

function selectSupplier(id, scroll = false) {
  const supplier = supplierById.get(clean(id));
  if (!supplier) return;
  selectedSupplierId = clean(id);
  renderDetail(supplier);
  renderRelatedPrices(relatedPricesForSupplier(supplier), `「${esc(supplier.name)}」の関連価格`);
  document.querySelectorAll(".supplier-card").forEach(card => card.classList.toggle("active", clean(card.dataset.supplierId) === selectedSupplierId));
  updateUrlSupplier(selectedSupplierId);
  if (scroll) {
    const card = document.getElementById(`supplier-${CSS.escape(selectedSupplierId)}`);
    if (card) card.scrollIntoView({behavior:"smooth", block:"center"});
  }
}

function renderPriceTable() {
  const filtered = allPrices.filter(p => matchesCategory(priceCategory(p), currentCategory));
  const fruitCount = filtered.filter(p => p._kind === "fruit").length;
  const generalCount = filtered.length - fruitCount;
  document.getElementById("priceTitle").textContent = `参考価格マスター：${label(currentCategory)}`;
  document.getElementById("priceCount").textContent = `${filtered.length}件（通常${generalCount}件・フルーツ${fruitCount}件）`;
  document.getElementById("priceTable").innerHTML = priceTableHtml(filtered, "master");
}

function priceTableHtml(list, prefix) {
  return `
    <table>
      <thead><tr>
        <th>カテゴリ</th><th>品目</th><th>区分</th><th>単位</th><th>件数</th>
        <th>中央値</th><th>平均</th><th>最小</th><th>最大</th><th>取得元</th><th>取得日</th>
      </tr></thead>
      <tbody>
        ${list.map(p => {
          const rowPrefix = p._kind || prefix || "master";
          const keyRaw = priceKey(p, rowPrefix);
          const key = esc(keyRaw);
          const selected = selectedPriceKey === keyRaw ? " price-selected" : "";
          return `<tr class="clickable${selected}" data-price-key="${key}" data-price-prefix="${esc(rowPrefix)}">
            <td>${esc(label(priceCategory(p)))}</td>
            <td>${esc(p.item_name)}</td>
            <td>${esc(p.product_form || "")}</td>
            <td>${esc(p.unit)}</td>
            <td>${yen(p.observation_count, 0)}</td>
            <td>¥${yen(p.median_unit_price_yen)}</td>
            <td>¥${yen(p.mean_unit_price_yen)}</td>
            <td>¥${yen(p.min_unit_price_yen)}</td>
            <td>¥${yen(p.max_unit_price_yen)}</td>
            <td>${sourceLinks(p.suppliers, p.source_urls)}</td>
            <td>${esc(p.latest_checked_date || "")}</td>
          </tr>`;
        }).join("") || `<tr><td colspan="11">該当する価格データがありません。</td></tr>`}
      </tbody>
    </table>`;
}

function findPriceByKey(key, prefix) {
  return allPrices.find(p => priceKey(p, p._kind || prefix || "master") === key);
}
function selectPriceRow(key, prefix) {
  const p = findPriceByKey(key, prefix);
  if (!p) return;
  selectedPriceKey = key;
  currentCategory = priceCategory(p);
  setActiveButtons(".filter", "category", currentCategory);
  const related = suppliersForPrice(p);
  renderSuppliers(related);
  renderPriceTable();
  renderRelatedPrices([p], `選択価格：${esc(p.item_name)} ${esc(p.product_form || "")} / 関連仕入先 ${related.length}件`);
  scrollPanelBodyToTop("supplierListBody");
}
function renderRelatedPrices(list, title = "関連価格") {
  const el = document.getElementById("relatedPrices");
  if (!list || !list.length) {
    el.innerHTML = `<div class="empty">関連する価格データがありません。</div>`;
    return;
  }
  el.innerHTML = `<div class="count">${title}：${list.length}件</div>${priceTableHtml(list.map(p => ({...p, category:p.category || "fruit"})), "related")}`;
}

function renderCompare() {
  const selected = [...compareIds].map(id => supplierById.get(id)).filter(Boolean).slice(0, 5);
  document.getElementById("compareCount").textContent = selected.length ? `${selected.length}件選択中（最大5件表示）` : "";
  if (!selected.length) {
    document.getElementById("compareTable").innerHTML = `<div class="empty">比較したい仕入先にチェックを入れてください。</div>`;
    return;
  }
  const rows = [
    ["名称", s => s.name],
    ["カテゴリ", s => label(s.source_category)],
    ["分類", s => s.type],
    ["取引形態", s => isOnline(s) ? "オンライン" : (s.local_or_online || "ローカル")],
    ["取扱", s => s.main_items],
    ["配送", s => s.delivery_available],
    ["店頭/引取", s => s.pickup_available],
    ["メモ", s => s.notes],
    ["公式", s => s.official_url ? `<a href="${esc(s.official_url)}" target="_blank" rel="noopener">開く</a>` : ""],
  ];
  document.getElementById("compareTable").innerHTML = `
    <div class="table-wrap"><table class="compare-table">
      <thead><tr><th>項目</th>${selected.map(s => `
        <th>
          <div>${esc(s.name)}</div>
          <button class="mini-btn remove-compare" data-remove-compare="${esc(s.supplier_id)}">比較から外す</button>
        </th>`).join("")}</tr></thead>
      <tbody>${rows.map(([name, fn]) => `<tr><th>${name}</th>${selected.map(s => `<td>${fn(s) || ""}</td>`).join("")}</tr>`).join("")}</tbody>
    </table></div>`;
  syncCompareCheckboxes();
}

function renderAll() {
  selectedPriceKey = null;
  renderSuppliers();
  renderPriceTable();
  renderCompare();
}


const panelDefaultHeights = {
  filterPanel: 520,
  supplierPanel: 520,
  pricePanel: 390,
  detailPanel: 430,
  relatedPanel: 330,
  comparePanel: 330,
};
const panelPresetHeights = {
  compact: 260,
  medium: 380,
  large: 560,
  full: null,
};
function clampPanelHeight(value) {
  const max = Math.max(320, window.innerHeight - 130);
  return Math.max(220, Math.min(max, value));
}
function clampPanelWidth(value) {
  const canvas = canvasEl ? canvasEl() : document.getElementById("dashboardCanvas");
  const max = Math.max(320, (canvas ? canvas.clientWidth : window.innerWidth) - 24);
  return Math.max(260, Math.min(max, value));
}
function setPanelWidth(panelId, width) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panel.style.setProperty("--panel-w", `${clampPanelWidth(width)}px`);
  if (typeof updateCanvasHeight === "function") updateCanvasHeight();
}
function setPanelHeight(panelId, height, preset = "custom") {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const nextHeight = height === null ? Math.max(320, window.innerHeight - 140) : clampPanelHeight(height);
  panel.style.setProperty("--panel-h", `${nextHeight}px`);
  panel.dataset.panelSize = preset;
  document.querySelectorAll(`[data-panel-controls="${CSS.escape(panelId)}"] .size-btn`).forEach(btn => {
    btn.classList.toggle("active", clean(btn.dataset.size) === preset);
  });
  if (typeof updateCanvasHeight === "function") updateCanvasHeight();
}
function resetPanelHeight(panelId) {
  setPanelHeight(panelId, panelDefaultHeights[panelId] || 380, "medium");
}
function initPanelSizeControls() {
  document.querySelectorAll(".size-controls .size-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const controls = btn.closest(".size-controls");
      const panelId = controls ? controls.dataset.panelControls : "";
      const size = clean(btn.dataset.size);
      if (!panelId) return;
      if (size === "reset") {
        resetPanelHeight(panelId);
        return;
      }
      const presetHeight = panelPresetHeights[size];
      setPanelHeight(panelId, presetHeight, size);
    });
  });

  document.querySelectorAll(".resize-grip").forEach(grip => {
    grip.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      const panelId = grip.dataset.resizePanel;
      const panel = document.getElementById(panelId);
      if (!panel) return;
      const startY = e.clientY;
      const startHeight = panel.getBoundingClientRect().height;
      grip.setPointerCapture(e.pointerId);
      const onMove = (moveEvent) => {
        const delta = moveEvent.clientY - startY;
        setPanelHeight(panelId, startHeight + delta, "custom");
      };
      const onUp = () => {
        grip.removeEventListener("pointermove", onMove);
        grip.removeEventListener("pointerup", onUp);
        grip.removeEventListener("pointercancel", onUp);
        if (typeof savePanelLayout === "function") savePanelLayout();
        if (typeof updateCanvasHeight === "function") updateCanvasHeight();
      };
      grip.addEventListener("pointermove", onMove);
      grip.addEventListener("pointerup", onUp);
      grip.addEventListener("pointercancel", onUp);
    });
  });
}


function initPanelResizeHandles() {
  document.querySelectorAll(".resize-side-grip, .resize-corner-grip").forEach(grip => {
    grip.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const panelId = grip.dataset.resizePanel;
      const dir = grip.dataset.resizeDir || "width";
      const panel = document.getElementById(panelId);
      if (!panel) return;

      bringPanelFront(panel);
      const startX = e.clientX;
      const startY = e.clientY;
      const startRect = panel.getBoundingClientRect();
      const startWidth = startRect.width;
      const startHeight = startRect.height;
      grip.setPointerCapture(e.pointerId);

      const onMove = (moveEvent) => {
        const dx = moveEvent.clientX - startX;
        const dy = moveEvent.clientY - startY;
        if (dir === "width" || dir === "both") {
          setPanelWidth(panelId, startWidth + dx);
        }
        if (dir === "both") {
          setPanelHeight(panelId, startHeight + dy, "custom");
        }
        updateCanvasHeight();
      };

      const onUp = () => {
        grip.removeEventListener("pointermove", onMove);
        grip.removeEventListener("pointerup", onUp);
        grip.removeEventListener("pointercancel", onUp);
        savePanelLayout();
        updateCanvasHeight();
      };

      grip.addEventListener("pointermove", onMove);
      grip.addEventListener("pointerup", onUp);
      grip.addEventListener("pointercancel", onUp);
    });
  });
}



const panelLayoutStorageKey = "procurementDashboardFreeLayoutV3";
const defaultPanelLayout = {
  filterPanel: { x: 18, y: 18, w: 300, h: 520 },
  supplierPanel: { x: 336, y: 154, w: 620, h: 520 },
  pricePanel: { x: 336, y: 692, w: 620, h: 390 },
  detailPanel: { x: 974, y: 154, w: 430, h: 430 },
  relatedPanel: { x: 974, y: 602, w: 430, h: 330 },
  comparePanel: { x: 974, y: 950, w: 430, h: 330 },
};
let topPanelZ = 20;

function panelIds() {
  return Object.keys(defaultPanelLayout);
}

function canvasEl() {
  return document.getElementById("dashboardCanvas") || document.querySelector(".layout");
}

function numericCssVar(panel, name, fallback) {
  const raw = getComputedStyle(panel).getPropertyValue(name).trim();
  const value = Number(String(raw).replace("px", ""));
  return Number.isFinite(value) ? value : fallback;
}

function setPanelBox(panelId, box = {}) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const def = defaultPanelLayout[panelId] || { x: 18, y: 18, w: 420, h: 380 };
  const x = Number.isFinite(Number(box.x)) ? Number(box.x) : def.x;
  const y = Number.isFinite(Number(box.y)) ? Number(box.y) : def.y;
  const w = Number.isFinite(Number(box.w)) ? Number(box.w) : def.w;
  const h = Number.isFinite(Number(box.h)) ? Number(box.h) : def.h;
  const z = Number.isFinite(Number(box.z)) ? Number(box.z) : undefined;

  panel.style.setProperty("--panel-x", `${Math.max(0, x)}px`);
  panel.style.setProperty("--panel-y", `${Math.max(0, y)}px`);
  panel.style.setProperty("--panel-w", `${Math.max(260, w)}px`);
  setPanelHeight(panelId, h, "custom");
  if (z !== undefined) panel.style.setProperty("--panel-z", String(z));
}

function getPanelBox(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return null;
  const rect = panel.getBoundingClientRect();
  return {
    x: numericCssVar(panel, "--panel-x", panel.offsetLeft),
    y: numericCssVar(panel, "--panel-y", panel.offsetTop),
    w: rect.width,
    h: rect.height,
    z: Number(panel.style.getPropertyValue("--panel-z") || 10),
  };
}

function savePanelLayout() {
  const layout = {};
  panelIds().forEach(id => {
    const box = getPanelBox(id);
    if (box) layout[id] = box;
  });
  try {
    localStorage.setItem(panelLayoutStorageKey, JSON.stringify(layout));
  } catch (err) {
    console.warn("layout save failed", err);
  }
}

function loadPanelLayout() {
  let loaded = null;
  try {
    const raw = localStorage.getItem(panelLayoutStorageKey);
    loaded = raw ? JSON.parse(raw) : null;
  } catch (err) {
    console.warn("layout load failed", err);
  }
  panelIds().forEach(id => setPanelBox(id, loaded && loaded[id] ? loaded[id] : defaultPanelLayout[id]));
  updateCanvasHeight();
}

function resetPanelLayout() {
  try { localStorage.removeItem(panelLayoutStorageKey); } catch (err) {}
  panelIds().forEach(id => setPanelBox(id, defaultPanelLayout[id]));
  updateCanvasHeight();
}

function bringPanelFront(panel) {
  topPanelZ += 1;
  panel.style.setProperty("--panel-z", String(topPanelZ));
}

function updateCanvasHeight() {
  const canvas = canvasEl();
  if (!canvas) return;
  let maxBottom = 0;
  panelIds().forEach(id => {
    const panel = document.getElementById(id);
    if (!panel || panel.offsetParent === null) return;
    const y = numericCssVar(panel, "--panel-y", panel.offsetTop);
    maxBottom = Math.max(maxBottom, y + panel.getBoundingClientRect().height + 40);
  });
  canvas.style.minHeight = `${Math.max(window.innerHeight - 72, maxBottom)}px`;
}

function initFreePanelDragging() {
  const canvas = canvasEl();
  if (!canvas) return;

  document.querySelectorAll(".scroll-panel[data-dashboard-panel]").forEach(panel => {
    panel.removeAttribute("draggable");
    const head = panel.querySelector(".panel-head");
    if (!head) return;

    head.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      if (e.target.closest("button,a,input,select,textarea,.size-controls,.resize-grip,.compare-check")) return;
      e.preventDefault();
      bringPanelFront(panel);
      panel.classList.add("free-dragging");
      head.setPointerCapture(e.pointerId);

      const canvasRect = canvas.getBoundingClientRect();
      const startX = e.clientX;
      const startY = e.clientY;
      const startPanelX = numericCssVar(panel, "--panel-x", panel.offsetLeft);
      const startPanelY = numericCssVar(panel, "--panel-y", panel.offsetTop);
      const panelWidth = panel.getBoundingClientRect().width;

      const onMove = (moveEvent) => {
        const dx = moveEvent.clientX - startX;
        const dy = moveEvent.clientY - startY;
        const maxX = Math.max(0, canvas.clientWidth - panelWidth - 8);
        const nextX = Math.min(maxX, Math.max(0, startPanelX + dx));
        const nextY = Math.max(0, startPanelY + dy);
        panel.style.setProperty("--panel-x", `${nextX}px`);
        panel.style.setProperty("--panel-y", `${nextY}px`);
        updateCanvasHeight();
      };

      const onUp = () => {
        panel.classList.remove("free-dragging");
        head.removeEventListener("pointermove", onMove);
        head.removeEventListener("pointerup", onUp);
        head.removeEventListener("pointercancel", onUp);
        savePanelLayout();
        updateCanvasHeight();
      };

      head.addEventListener("pointermove", onMove);
      head.addEventListener("pointerup", onUp);
      head.addEventListener("pointercancel", onUp);
    });
  });

  const resetBtn = document.getElementById("resetLayoutBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", e => {
      e.preventDefault();
      resetPanelLayout();
    });
  }

  window.addEventListener("resize", updateCanvasHeight);
  loadPanelLayout();
}

function initDraggablePanels() {
  initFreePanelDragging();
}

// events
document.querySelectorAll(".filter").forEach(btn => btn.addEventListener("click", () => {
  currentCategory = btn.dataset.category;
  setActiveButtons(".filter", "category", currentCategory);
  renderAll();
}));
document.querySelectorAll(".scope").forEach(btn => btn.addEventListener("click", () => {
  currentScope = btn.dataset.scope;
  setActiveButtons(".scope", "scope", currentScope);
  renderAll();
}));
document.querySelectorAll(".item-filter").forEach(btn => btn.addEventListener("click", () => {
  itemKeyword = btn.dataset.item || "";
  document.querySelectorAll(".item-filter").forEach(b => b.classList.toggle("active", b === btn));
  renderAll();
}));
document.getElementById("searchBox").addEventListener("input", () => renderSuppliers());
document.getElementById("sortSelect").addEventListener("change", () => renderSuppliers());
document.getElementById("clearAllBtn").addEventListener("click", () => {
  currentCategory = "all"; currentScope = "all"; itemKeyword = ""; selectedPriceKey = null;
  document.getElementById("searchBox").value = "";
  setActiveButtons(".filter", "category", "all");
  setActiveButtons(".scope", "scope", "all");
  document.querySelectorAll(".item-filter").forEach((b, i) => b.classList.toggle("active", i === 0));
  renderAll();
});
document.body.addEventListener("click", (e) => {
  if (e.target.closest("a")) return;
  const removeCompare = e.target.closest(".remove-compare");
  if (removeCompare) {
    const id = clean(removeCompare.dataset.removeCompare);
    compareIds.delete(id);
    renderCompare();
    return;
  }
  const compare = e.target.closest(".compare-check");
  if (compare) {
    const id = clean(compare.dataset.compareId);
    if (compare.checked) compareIds.add(id); else compareIds.delete(id);
    renderCompare();
    return;
  }
  const detailBtn = e.target.closest(".select-detail");
  if (detailBtn) { selectSupplier(detailBtn.dataset.supplierId, false); return; }
  const card = e.target.closest(".supplier-card");
  if (card) { selectSupplier(card.dataset.supplierId, false); return; }
  const priceRow = e.target.closest("tr[data-price-key]");
  if (priceRow) { selectPriceRow(priceRow.dataset.priceKey, priceRow.dataset.pricePrefix); return; }
});

initPanelSizeControls();
initPanelResizeHandles();
initDraggablePanels();
renderAll();
const params = new URLSearchParams(window.location.search);
const initialSupplierId = clean(params.get("supplier_id"));
if (initialSupplierId && supplierById.has(initialSupplierId)) {
  selectSupplier(initialSupplierId, true);
}
</script>
</body>
</html>
'''


def build_html(suppliers: list[dict], prices: list[dict], fruit_prices: list[dict]) -> str:
    stats = build_stats(suppliers, prices, fruit_prices)
    html = HTML_TEMPLATE
    replacements = {
        "__SUPPLIERS_JSON__": json.dumps(suppliers, ensure_ascii=False, allow_nan=False),
        "__PRICES_JSON__": json.dumps(prices, ensure_ascii=False, allow_nan=False),
        "__FRUIT_PRICES_JSON__": json.dumps(fruit_prices, ensure_ascii=False, allow_nan=False),
        "__CATEGORY_LABELS_JSON__": json.dumps(CATEGORY_LABELS, ensure_ascii=False, allow_nan=False),
        "__SUPPLIER_TOTAL__": str(stats["supplier_total"]),
        "__LOCAL_COUNT__": str(stats["local_count"]),
        "__ONLINE_COUNT__": str(stats["online_count"]),
        "__PRICE_TOTAL__": str(stats["price_total"]),
        "__FRUIT_PRICE_TOTAL__": str(stats["fruit_price_total"]),
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suppliers = load_csv("supplier_master.csv", SUPPLIER_COLUMNS)
    prices = load_csv("price_master.csv", PRICE_COLUMNS)
    fruit_prices = load_csv("fruit_price_master.csv", FRUIT_PRICE_COLUMNS)
    html = build_html(suppliers, prices, fruit_prices)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[SAVE] {OUT_PATH}")
    print("[SUPPLIERS]", len(suppliers))
    print("[PRICES]", len(prices))
    print("[FRUIT_PRICES]", len(fruit_prices))


if __name__ == "__main__":
    main()
