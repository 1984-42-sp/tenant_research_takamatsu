from pathlib import Path
import json
import math
import pandas as pd

SCRIPT_VERSION = "2026-06-27-collapsible-evidence-v4"

BASE_DIR = Path(__file__).resolve().parents[1]

RECIPE_DIR = BASE_DIR / "data" / "recipes"
MASTER_DIR = BASE_DIR / "output" / "master"
OUT_DIR = BASE_DIR / "output" / "dashboard"
OUT_PATH = OUT_DIR / "cost_simulator_dashboard.html"

UNIT_ALIASES = {
    "kg": "kg", "ｋｇ": "kg", "キロ": "kg",
    "g": "g", "ｇ": "g", "グラム": "g",
    "L": "L", "l": "L", "Ｌ": "L", "リットル": "L",
    "ml": "ml", "mL": "ml", "ML": "ml", "ｍｌ": "ml", "ミリリットル": "ml",
    "個": "個", "本": "本", "枚": "枚", "杯": "杯", "食": "食",
}

UNIT_CONVERSIONS = {
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    ("ml", "L"): 0.001,
    ("L", "ml"): 1000.0,
}

CATEGORY_LABELS = {
    "drink": "ドリンク",
    "food": "フード",
    "sweets": "スイーツ",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARN] missing: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig").fillna("")


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def to_float(value, default: float = 0.0) -> float:
    text = clean(value).replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def normalize_unit(unit: str) -> str:
    text = clean(unit)
    return UNIT_ALIASES.get(text, text)


def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> tuple[float, bool, str]:
    src = normalize_unit(from_unit)
    dst = normalize_unit(to_unit)

    if not src or not dst:
        return quantity, False, "単位未設定"
    if src == dst:
        return quantity, True, ""

    factor = UNIT_CONVERSIONS.get((src, dst))
    if factor is not None:
        return quantity * factor, True, ""

    return quantity, False, f"単位換算未対応: {src} → {dst}"


def joined_preview(value: str, max_items: int = 4) -> dict:
    items = [x.strip() for x in clean(value).split(" / ") if x.strip()]
    return {
        "items": items,
        "preview": " / ".join(items[:max_items]),
        "hidden_count": max(0, len(items) - max_items),
        "count": len(items),
    }


def add_price(
    price_lookup: dict,
    source: str,
    key: str,
    unit_price,
    unit,
    suppliers,
    source_urls="",
    observation_count="",
) -> None:
    source = clean(source)
    key = clean(key)
    if not source or not key:
        return

    price_lookup[(source, key)] = {
        "unit_price": to_float(unit_price),
        "unit": normalize_unit(unit),
        "suppliers": clean(suppliers),
        "source_urls": clean(source_urls),
        "observation_count": int(to_float(observation_count, 0)),
    }


def load_price_lookup(prices: pd.DataFrame, fruit_prices: pd.DataFrame) -> dict:
    price_lookup = {}

    if not prices.empty:
        for _, r in prices.iterrows():
            add_price(
                price_lookup,
                "general",
                r.get("item_name"),
                r.get("median_unit_price_yen"),
                r.get("unit"),
                r.get("suppliers"),
                r.get("source_urls"),
                r.get("observation_count"),
            )

    if not fruit_prices.empty:
        for _, r in fruit_prices.iterrows():
            add_price(
                price_lookup,
                "fruit",
                r.get("item_name"),
                r.get("median_unit_price_yen"),
                r.get("unit"),
                r.get("suppliers"),
                r.get("source_urls"),
                r.get("observation_count"),
            )

    return price_lookup


def evidence_for_price(price_info: dict) -> dict:
    """Screen-facing wording. Do not leak implementation terms such as CSV/master names."""
    if price_info:
        observation_count = int(to_float(price_info.get("observation_count"), 0))
        if observation_count >= 3:
            return {
                "basis": "市場調査価格",
                "basis_short": f"{observation_count}件の調査価格から算出",
                "basis_detail": f"{observation_count}件の調査価格から中央値を採用しています。",
                "confidence_label": "高",
                "confidence_stars": "★★★★★",
                "confidence_detail": "複数価格を比較済み",
            }
        if observation_count > 0:
            return {
                "basis": "参考価格",
                "basis_short": "調査件数が少ないため参考値",
                "basis_detail": f"調査件数が{observation_count}件のため、現時点では参考値として扱います。",
                "confidence_label": "中",
                "confidence_stars": "★★★☆☆",
                "confidence_detail": "追加確認推奨",
            }
        return {
            "basis": "参考価格",
            "basis_short": "調査件数が少ないため参考値",
            "basis_detail": "調査価格はありますが、件数情報が不足しているため参考値として扱います。",
            "confidence_label": "中",
            "confidence_stars": "★★★☆☆",
            "confidence_detail": "追加確認推奨",
        }

    return {
        "basis": "設定価格",
        "basis_short": "まだ調査できていないため仮設定",
        "basis_detail": "まだ調査できていないため、開業計画作成用の仮設定として扱います。",
        "confidence_label": "要確認",
        "confidence_stars": "★☆☆☆☆",
        "confidence_detail": "実仕入価格の確認が必要",
    }


def load_ingredients(ingredients: pd.DataFrame, price_lookup: dict) -> dict:
    ingredients_by_id = {}

    for _, r in ingredients.iterrows():
        ingredient_id = clean(r.get("ingredient_id"))
        if not ingredient_id:
            continue

        source = clean(r.get("price_source")) or "manual"
        key = clean(r.get("price_key"))
        ref_price = to_float(r.get("reference_unit_price_yen"))
        ref_unit = normalize_unit(r.get("reference_unit"))

        price_info = price_lookup.get((source, key), {})
        evidence = evidence_for_price(price_info)

        unit_price = to_float(price_info.get("unit_price"), ref_price) or ref_price
        price_unit = normalize_unit(price_info.get("unit") or ref_unit)
        suppliers = clean(price_info.get("suppliers")) or clean(r.get("preferred_supplier_hint"))
        source_urls = clean(price_info.get("source_urls"))
        observation_count = int(to_float(price_info.get("observation_count"), 0)) if price_info else 0

        ingredients_by_id[ingredient_id] = {
            "ingredient_id": ingredient_id,
            "ingredient_name": clean(r.get("ingredient_name")),
            "price_source_internal": source,
            "price_key_internal": key,
            "unit_price": unit_price,
            "price_unit": price_unit,
            "suppliers": suppliers,
            "supplier_preview": joined_preview(suppliers),
            "source_urls": source_urls,
            "source_url_preview": joined_preview(source_urls),
            "observation_count": observation_count,
            **evidence,
            "notes": clean(r.get("notes")),
        }

    return ingredients_by_id


def load_data():
    menus = read_csv(RECIPE_DIR / "menu_master.csv")
    ingredients = read_csv(RECIPE_DIR / "ingredient_master.csv")
    recipes = read_csv(RECIPE_DIR / "recipe_master.csv")
    prices = read_csv(MASTER_DIR / "price_master.csv")
    fruit_prices = read_csv(MASTER_DIR / "fruit_price_master.csv")

    price_lookup = load_price_lookup(prices, fruit_prices)
    ingredients_by_id = load_ingredients(ingredients, price_lookup)

    menu_records = []
    for _, menu in menus.iterrows():
        menu_id = clean(menu.get("menu_id"))
        if not menu_id:
            continue

        if "menu_id" not in recipes.columns:
            rows = pd.DataFrame()
        else:
            rows = recipes[recipes["menu_id"].astype(str).str.strip() == menu_id]

        ingredients_list = []
        total_cost = 0.0
        warnings = []

        for _, rr in rows.iterrows():
            ing = ingredients_by_id.get(clean(rr.get("ingredient_id")))
            if not ing:
                warnings.append(f"未登録材料ID: {clean(rr.get('ingredient_id'))}")
                continue

            quantity = to_float(rr.get("quantity"))
            recipe_unit = normalize_unit(rr.get("unit"))
            price_unit = normalize_unit(ing["price_unit"])
            waste_rate = to_float(rr.get("waste_rate"))

            converted_quantity, conversion_ok, warning = convert_quantity(quantity, recipe_unit, price_unit)
            if warning:
                warnings.append(f"{ing['ingredient_name']}: {warning}")

            cost = converted_quantity * ing["unit_price"] * (1 + waste_rate)
            total_cost += cost

            ingredients_list.append({
                **ing,
                "quantity": quantity,
                "unit": recipe_unit,
                "converted_quantity": converted_quantity,
                "conversion_ok": conversion_ok,
                "conversion_warning": warning,
                "waste_rate": waste_rate,
                "cost": cost,
                "recipe_notes": clean(rr.get("notes")),
            })

        sales_price = to_float(menu.get("default_sales_price_yen"))
        monthly_sales = to_float(menu.get("default_monthly_sales"))
        gross_profit = sales_price - total_cost
        cost_rate = total_cost / sales_price * 100 if sales_price else 0

        menu_records.append({
            "menu_id": menu_id,
            "menu_name": clean(menu.get("menu_name")),
            "category": clean(menu.get("category")),
            "category_label": CATEGORY_LABELS.get(clean(menu.get("category")), clean(menu.get("category"))),
            "sales_price": sales_price,
            "monthly_sales": monthly_sales,
            "total_cost": total_cost,
            "cost_rate": cost_rate,
            "gross_profit": gross_profit,
            "monthly_revenue": sales_price * monthly_sales,
            "monthly_cost": total_cost * monthly_sales,
            "monthly_gross_profit": gross_profit * monthly_sales,
            "ingredients": ingredients_list,
            "warnings": list(dict.fromkeys(warnings)),
        })

    return menu_records


HTML = r'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>カフェメニュー原価シミュレーター</title>
<style>
:root{--brown:#2f241d;--paper:#f6f4ef;--cream:#f3eee7;--line:#e8e1d8;--muted:#666;--warn:#fff8df;--ok:#356b2d;--mid:#7a5a00;--low:#8a3b2a}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--paper);color:#222}
header{background:var(--brown);color:white;padding:18px 24px}
h1{margin:0;font-size:24px}
header p{margin:6px 0 0;color:#ddd;font-size:13px}
.layout{display:grid;grid-template-columns:280px 1fr;gap:18px;padding:18px;align-items:start}
.panel{background:white;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.08);padding:16px}
.sidebar{position:sticky;top:18px}
.menu-btn{width:100%;padding:10px;margin:5px 0;border:1px solid #ddd;border-radius:10px;background:#fafafa;text-align:left;cursor:pointer}
.menu-btn.active{background:var(--brown);color:white}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.stat{background:#fbf7f1;border-radius:12px;padding:14px}.stat .num{font-size:24px;font-weight:800}.stat .label{font-size:12px;color:#666}
input{width:100%;padding:9px;border:1px solid #ddd;border-radius:8px;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:14px;background:white}th,td{border-bottom:1px solid #eee;padding:9px;text-align:left;vertical-align:top}th{background:var(--cream)}
.control-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 18px}.small{font-size:12px;color:#666}.badge{display:inline-block;background:#eee2d2;border-radius:999px;padding:3px 8px;font-size:12px;margin-right:4px}.notice{background:var(--warn);border:1px solid #f0dfa9;border-radius:12px;padding:10px;margin:10px 0;font-size:13px;color:#5b481a}.warn{color:#9a5b00}.table-wrap{overflow:auto;border:1px solid #eee;border-radius:12px}.source{font-size:12px;color:#666}.basis-badge{display:inline-block;border-radius:999px;background:#e8e1d8;padding:3px 8px;font-size:12px;font-weight:700}.basis-badge.market{background:#e1edd8;color:#234d1f}.basis-badge.reference{background:#fff0c2;color:#5b481a}.basis-badge.setting{background:#f2dfd8;color:#6d2e20}.basis-short{font-size:12px;color:#666;margin-top:3px}.confidence{font-weight:800;letter-spacing:.03em}.confidence-detail{font-size:12px;color:#666;margin-top:3px}.supplier-summary{font-size:13px}.supplier-count{font-size:12px;color:#666;margin-top:3px}.legend{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.legend span{display:inline-block;border:1px solid #eee;border-radius:999px;background:#fafafa;padding:5px 10px;font-size:12px;color:#555}
details.evidence{margin-top:6px;font-size:12px;color:#444}details.evidence summary{cursor:pointer;color:#0645ad;list-style:none;display:inline-block;border:1px solid #ddd;border-radius:999px;padding:3px 8px;background:#fafafa}details.evidence summary::-webkit-details-marker{display:none}details.evidence[open] summary{background:#f7f1e9}.evidence-box{margin-top:8px;padding:8px;border:1px solid #eee;border-radius:10px;background:#fff}.evidence-grid{display:grid;grid-template-columns:86px 1fr;gap:5px 8px}.evidence-label{color:#777}.evidence-list{margin:4px 0 0;padding-left:18px}.nowrap{white-space:nowrap}
@media(max-width:1000px){.layout{grid-template-columns:1fr}.sidebar{position:static}.grid{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header>
  <h1>カフェメニュー原価シミュレーター</h1>
  <p>調査した仕入価格とメニュー構成をもとに、1杯/1食あたり原価と月間粗利を試算します。</p>
</header>

<div class="layout">
  <aside class="panel sidebar">
    <h2>メニュー選択</h2>
    <div id="menuList"></div>
  </aside>

  <main>
    <section class="panel">
      <h2 id="menuTitle"></h2>
      <div><span class="badge" id="menuCategory"></span></div>
      <div id="warningBox"></div>

      <div class="legend">
        <span><strong>市場調査価格</strong>：複数の調査価格から算出</span>
        <span><strong>参考価格</strong>：調査件数が少ないため参考値</span>
        <span><strong>設定価格</strong>：まだ調査できていないため仮設定</span>
      </div>

      <div class="control-grid">
        <label>想定販売価格（円）<input id="salesPriceInput" type="number" min="0" step="10"></label>
        <label>月間販売数<input id="monthlySalesInput" type="number" min="0" step="1"></label>
      </div>

      <div class="grid">
        <div class="stat"><div class="num" id="totalCost"></div><div class="label">1杯/1食あたり原価</div></div>
        <div class="stat"><div class="num" id="costRate"></div><div class="label">原価率</div></div>
        <div class="stat"><div class="num" id="grossProfit"></div><div class="label">粗利</div></div>
        <div class="stat"><div class="num" id="monthlyGrossProfit"></div><div class="label">月間粗利</div></div>
      </div>

      <h3>材料別原価</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>材料</th><th>使用量</th><th>計算数量</th><th>採用単価</th><th>ロス率</th><th>原価</th><th>価格根拠</th><th>信頼度</th><th>主な調査先</th>
            </tr>
          </thead>
          <tbody id="ingredientRows"></tbody>
        </table>
      </div>

      <h3>月間試算</h3>
      <table>
        <tbody>
          <tr><th>月間売上</th><td id="monthlyRevenue"></td></tr>
          <tr><th>月間原価</th><td id="monthlyCost"></td></tr>
          <tr><th>月間粗利</th><td id="monthlyGrossProfit2"></td></tr>
        </tbody>
      </table>

      <p class="small">価格根拠は「市場調査価格」「参考価格」「設定価格」の3段階で表示します。信頼度が低い材料から、実際の仕入先・見積価格を確認してください。単位換算は g↔kg、ml↔L に対応しています。</p>
    </section>
  </main>
</div>

<script>
const menus = __MENUS_JSON__;
let current = menus[0] || null;

function yen(v){return "¥" + Math.round(Number(v || 0)).toLocaleString("ja-JP");}
function yen2(v){return "¥" + Number(v || 0).toLocaleString("ja-JP", {maximumFractionDigits:2});}
function pct(v){return Number(v || 0).toFixed(1) + "%";}
function num(v){return Number(v || 0).toLocaleString("ja-JP", {maximumFractionDigits:4});}
function esc(v){return String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
function basisClass(v){if(v === "市場調査価格") return "market"; if(v === "参考価格") return "reference"; return "setting";}
function sourceItems(value){return String(value || "").split(" / ").map(s => s.trim()).filter(Boolean);}
function supplierSummary(v){
  const list = sourceItems(v);
  if (!list.length) return "未調査";
  const shown = list.slice(0, 2).map(esc).join(" / ");
  const rest = list.length > 2 ? `<div class="supplier-count">ほか${list.length - 2}件</div>` : "";
  return `<div class="supplier-summary">${shown}</div>${rest}`;
}
function sourceListHtml(v){
  const list = sourceItems(v);
  if (!list.length) return "未調査";
  return `<ul class="evidence-list">${list.map(x => `<li>${esc(x)}</li>`).join("")}</ul>`;
}
function evidenceDetails(i){
  return `
    <details class="evidence">
      <summary>詳細</summary>
      <div class="evidence-box">
        <div class="evidence-grid">
          <div class="evidence-label">価格根拠</div><div>${esc(i.basis_detail || i.basis_short || "")}</div>
          <div class="evidence-label">調査件数</div><div>${Number(i.observation_count || 0) > 0 ? esc(i.observation_count) + "件" : "未調査"}</div>
          <div class="evidence-label">採用方法</div><div>${i.basis === "市場調査価格" ? "中央値" : i.basis === "参考価格" ? "参考値" : "仮設定"}</div>
          <div class="evidence-label">調査先</div><div>${sourceListHtml(i.suppliers)}</div>
        </div>
      </div>
    </details>`;
}

function renderMenuList(){
  document.getElementById("menuList").innerHTML = menus.map(m => `
    <button class="menu-btn ${current && m.menu_id === current.menu_id ? "active" : ""}" data-id="${esc(m.menu_id)}">${esc(m.menu_name)}</button>
  `).join("");
}

function renderWarnings(){
  const box = document.getElementById("warningBox");
  if (!current || !current.warnings || !current.warnings.length) { box.innerHTML = ""; return; }
  box.innerHTML = `<div class="notice"><strong>確認事項</strong><br>${current.warnings.map(esc).join("<br>")}</div>`;
}

function render(){
  if (!current) return;
  renderMenuList();
  renderWarnings();

  const salesPrice = Number(document.getElementById("salesPriceInput").value || current.sales_price);
  const monthlySales = Number(document.getElementById("monthlySalesInput").value || current.monthly_sales);
  const totalCost = Number(current.total_cost || 0);
  const grossProfit = salesPrice - totalCost;
  const costRate = salesPrice ? totalCost / salesPrice * 100 : 0;

  document.getElementById("menuTitle").textContent = current.menu_name;
  document.getElementById("menuCategory").textContent = current.category_label || current.category;
  document.getElementById("salesPriceInput").value = salesPrice;
  document.getElementById("monthlySalesInput").value = monthlySales;

  document.getElementById("totalCost").textContent = yen(totalCost);
  document.getElementById("costRate").textContent = pct(costRate);
  document.getElementById("grossProfit").textContent = yen(grossProfit);
  document.getElementById("monthlyRevenue").textContent = yen(salesPrice * monthlySales);
  document.getElementById("monthlyCost").textContent = yen(totalCost * monthlySales);
  document.getElementById("monthlyGrossProfit").textContent = yen(grossProfit * monthlySales);
  document.getElementById("monthlyGrossProfit2").textContent = yen(grossProfit * monthlySales);

  document.getElementById("ingredientRows").innerHTML = current.ingredients.map(i => `
    <tr>
      <td>${esc(i.ingredient_name)}${i.conversion_warning ? `<div class="source warn">${esc(i.conversion_warning)}</div>` : ""}</td>
      <td class="nowrap">${num(i.quantity)} ${esc(i.unit)}</td>
      <td class="nowrap">${num(i.converted_quantity)} ${esc(i.price_unit)}</td>
      <td class="nowrap">${yen2(i.unit_price)} / ${esc(i.price_unit)}</td>
      <td>${pct(i.waste_rate * 100)}</td>
      <td><strong>${yen(i.cost)}</strong></td>
      <td><span class="basis-badge ${basisClass(i.basis)}">${esc(i.basis)}</span><div class="basis-short">${esc(i.basis_short || "")}</div>${evidenceDetails(i)}</td>
      <td><div class="confidence">${esc(i.confidence_stars || "")}</div><div class="confidence-detail">${esc(i.confidence_label || "")}：${esc(i.confidence_detail || "")}</div></td>
      <td>${supplierSummary(i.suppliers)}</td>
    </tr>
  `).join("");
}

document.body.addEventListener("click", e => {
  const btn = e.target.closest(".menu-btn");
  if (!btn) return;
  current = menus.find(m => m.menu_id === btn.dataset.id) || menus[0];
  document.getElementById("salesPriceInput").value = current.sales_price;
  document.getElementById("monthlySalesInput").value = current.monthly_sales;
  render();
});

document.getElementById("salesPriceInput").addEventListener("input", render);
document.getElementById("monthlySalesInput").addEventListener("input", render);

if (current) {
  document.getElementById("salesPriceInput").value = current.sales_price;
  document.getElementById("monthlySalesInput").value = current.monthly_sales;
  render();
}
</script>
</body>
</html>
'''


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    menus = load_data()
    html = HTML.replace("__MENUS_JSON__", json.dumps(menus, ensure_ascii=False, allow_nan=False))
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[SAVE] {OUT_PATH}")
    print(f"[MENUS] {len(menus)}")
    print(f"[VERSION] {SCRIPT_VERSION}")


if __name__ == "__main__":
    main()
