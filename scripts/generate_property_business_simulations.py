from pathlib import Path
from html import escape
import math
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"
OUT_DIR = BASE_DIR / "output" / "all_properties" / "property_business_simulations"
INDEX_HTML = OUT_DIR / "index.html"


SALES_DAYS = 26
WEEKDAYS = 18
WEEKENDS = 8


def safe(value):
    if pd.isna(value):
        return ""
    return str(value)


def num(value, default=None):
    try:
        if pd.isna(value) or value == "":
            return default
        return float(value)
    except Exception:
        return default


def yen(value):
    v = num(value)
    if v is None:
        return ""
    return f"{int(round(v)):,}円"


def people(value):
    v = num(value)
    if v is None:
        return ""
    return f"{int(round(v))}人"


def pct(value):
    if value is None:
        return ""
    return f"{round(value * 100)}%"


def slugify(text, index):
    text = safe(text)
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"\s+", "_", text).strip("_")
    return f"{index:03d}_{text[:40]}.html"


def classify_menu_strategy(row):
    pattern = safe(row.get("事業成立パターン"))
    location = safe(row.get("立地区分"))
    seats = num(row.get("推定席数"), 0)
    customers = num(row.get("推奨必要日客数"), 0)

    if pattern == "中心街・高単価型":
        return "パフェ主導・目的来店型"

    if pattern == "中心街・高回転型":
        return "ドリンク強化・回転型"

    if pattern == "低固定費・小商圏型":
        return "ドリンク主導・小商圏型"

    if pattern == "準中心街・生活圏型":
        return "バランス型"

    if pattern == "郊外・駐車場依存型":
        return "パフェ・滞在型"

    if pattern == "大型投資・高売上必須型":
        return "複合大型型"

    if location == "中心街" and seats <= 15:
        return "パフェ主導・目的来店型"

    if customers <= 30:
        return "ドリンク主導・小商圏型"

    return "要個別検討"


def get_menu_mix(strategy):
    mixes = {
        "パフェ主導・目的来店型": {
            "パフェ": 0.45,
            "フルーツドリンク": 0.25,
            "コーヒー": 0.20,
            "その他": 0.10,
        },
        "ドリンク強化・回転型": {
            "パフェ": 0.20,
            "フルーツドリンク": 0.35,
            "コーヒー": 0.35,
            "その他": 0.10,
        },
        "ドリンク主導・小商圏型": {
            "パフェ": 0.20,
            "フルーツドリンク": 0.35,
            "コーヒー": 0.35,
            "その他": 0.10,
        },
        "バランス型": {
            "パフェ": 0.35,
            "フルーツドリンク": 0.30,
            "コーヒー": 0.25,
            "その他": 0.10,
        },
        "パフェ・滞在型": {
            "パフェ": 0.40,
            "フルーツドリンク": 0.25,
            "コーヒー": 0.25,
            "その他": 0.10,
        },
        "複合大型型": {
            "パフェ": 0.35,
            "フルーツドリンク": 0.30,
            "コーヒー": 0.25,
            "その他": 0.10,
        },
        "要個別検討": {
            "パフェ": 0.30,
            "フルーツドリンク": 0.30,
            "コーヒー": 0.30,
            "その他": 0.10,
        },
    }
    return mixes.get(strategy, mixes["要個別検討"])


def estimate_item_prices(strategy):
    if strategy == "パフェ主導・目的来店型":
        return {
            "パフェ": 1500,
            "フルーツドリンク": 780,
            "コーヒー": 600,
            "その他": 500,
        }

    if strategy in ["パフェ・滞在型", "バランス型"]:
        return {
            "パフェ": 1400,
            "フルーツドリンク": 750,
            "コーヒー": 580,
            "その他": 500,
        }

    return {
        "パフェ": 1200,
        "フルーツドリンク": 700,
        "コーヒー": 550,
        "その他": 450,
    }


def estimate_average_price(menu_mix, prices):
    return sum(menu_mix[k] * prices[k] for k in menu_mix)


def estimate_weekday_weekend_customers(recommended_daily):
    if recommended_daily is None:
        return None, None

    # 休日は平日の約1.6倍として、26営業日で推奨日客数平均に合うように配分
    weekday = recommended_daily * SALES_DAYS / (WEEKDAYS + WEEKENDS * 1.6)
    weekend = weekday * 1.6

    return round(weekday), round(weekend)


def estimate_staff_plan(row, menu_mix):
    customers = num(row.get("推奨必要日客数"))
    seats = num(row.get("推定席数"), 0)

    if customers is None:
        return "要確認", "必要客数が不明のため、人員計画は要確認です。"

    parfait_ratio = menu_mix.get("パフェ", 0)
    fruit_drink_ratio = menu_mix.get("フルーツドリンク", 0)
    coffee_ratio = menu_mix.get("コーヒー", 0)

    production_load = (
        parfait_ratio * 3.0
        + fruit_drink_ratio * 2.0
        + coffee_ratio * 1.0
    )

    if customers <= 30 and production_load < 1.8:
        return (
            "2名体制",
            "常時2名出勤。注文・会計・コーヒー担当と、フルーツドリンク・パフェ製造担当で分担。ワンオペは採用しない前提です。"
        )

    if customers <= 40:
        return (
            "2名体制＋ピーク補助",
            "基本は2名体制。土日やピーク時間帯は3名体制を検討。パフェ・フルーツドリンクの製造が重なる時間帯に滞留が出やすい想定です。"
        )

    if customers <= 65:
        return (
            "3名体制",
            "平日2〜3名、休日3名体制。会計・提供、ドリンク、パフェ・仕込み補充を分担する前提です。"
        )

    if customers <= 90:
        return (
            "3〜4名体制",
            "常時3名、休日ピーク4名を想定。カウンター内完結型でも、製造と会計提供を分けないと待ち時間が長くなります。"
        )

    return (
        "4名以上",
        "多客数前提。会計、コーヒー、フルーツドリンク、パフェ、補充・洗い物の分担が必要です。個人小規模開業としては高難度です。"
    )


def estimate_summer_boost(row, menu_mix):
    pattern = safe(row.get("事業成立パターン"))
    parfait_ratio = menu_mix.get("パフェ", 0)

    if pattern in ["中心街・高単価型", "郊外・駐車場依存型"]:
        base = 0.30
    elif pattern in ["準中心街・生活圏型", "低固定費・小商圏型"]:
        base = 0.22
    else:
        base = 0.15

    if parfait_ratio >= 0.35:
        base += 0.05

    return min(base, 0.40)


def build_sales_breakdown(monthly_sales, menu_mix):
    rows = []
    for name, ratio in menu_mix.items():
        rows.append({
            "name": name,
            "ratio": ratio,
            "sales": monthly_sales * ratio if monthly_sales else None,
        })
    return rows


def make_html(row, index, file_name):
    name = safe(row.get("物件名"))
    strategy = classify_menu_strategy(row)
    menu_mix = get_menu_mix(strategy)
    prices = estimate_item_prices(strategy)
    average_price = estimate_average_price(menu_mix, prices)

    monthly_sales = num(row.get("必要月商"))
    daily_sales = num(row.get("必要日商_26日営業"))
    theoretical_customers = num(row.get("理論必要日客数"))
    recommended_customers = num(row.get("推奨必要日客数"))
    seats = num(row.get("推定席数"))

    weekday_customers, weekend_customers = estimate_weekday_weekend_customers(
        recommended_customers
    )

    staff_title, staff_comment = estimate_staff_plan(row, menu_mix)
    summer_boost = estimate_summer_boost(row, menu_mix)
    summer_sales = monthly_sales * (1 + summer_boost) if monthly_sales else None

    cost_rate = num(row.get("原価率"), 0.32)
    labor_rate = num(row.get("人件費率"), 0.26)
    rent = num(row.get("家賃_円"), 0)
    other_fixed = num(row.get("その他固定費"), 0)

    food_cost = monthly_sales * cost_rate if monthly_sales else None
    labor_cost = monthly_sales * labor_rate if monthly_sales else None
    operating_profit = (
        monthly_sales - food_cost - labor_cost - rent - other_fixed
        if monthly_sales is not None
        else None
    )

    sales_breakdown = build_sales_breakdown(monthly_sales, menu_mix)

    detail_url = safe(row.get("詳細URL"))
    detail_link = (
        f'<a href="{escape(detail_url)}" target="_blank">物件詳細ページ</a>'
        if detail_url
        else "詳細URLなし"
    )

    menu_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(item["name"])}</td>
          <td>{pct(item["ratio"])}</td>
          <td>{yen(item["sales"])}</td>
          <td>{yen(prices[item["name"]])}</td>
        </tr>
        """
        for item in sales_breakdown
    )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{escape(name)} 営業シミュレーション</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  background: #f4f5f7;
  color: #222;
}}
.header {{
  background: #2f3a45;
  color: white;
  padding: 28px 36px;
}}
.header h1 {{
  margin: 0 0 8px 0;
  font-size: 28px;
}}
.header .sub {{
  opacity: 0.9;
}}
.container {{
  padding: 28px 36px;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}}
.card {{
  background: white;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.card .label {{
  color: #666;
  font-size: 13px;
}}
.card .value {{
  font-size: 22px;
  font-weight: 700;
  margin-top: 6px;
}}
.section {{
  background: white;
  border-radius: 10px;
  padding: 22px;
  margin: 18px 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.section h2 {{
  margin-top: 0;
  border-bottom: 2px solid #eee;
  padding-bottom: 8px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
}}
th, td {{
  border-bottom: 1px solid #e5e5e5;
  padding: 10px;
  text-align: left;
}}
th {{
  background: #fafafa;
}}
.badge {{
  display: inline-block;
  background: #eef3f8;
  border-radius: 999px;
  padding: 5px 10px;
  margin: 2px 4px 2px 0;
  font-size: 13px;
}}
.warn {{
  background: #fff8e6;
  border-left: 5px solid #e0a800;
  padding: 14px 16px;
  line-height: 1.7;
}}
.good {{
  background: #eef9f0;
  border-left: 5px solid #3fa35c;
  padding: 14px 16px;
  line-height: 1.7;
}}
a {{
  color: #0066cc;
}}
</style>
</head>
<body>

<div class="header">
  <h1>{escape(name)}</h1>
  <div class="sub">物件別営業シミュレーション / フルーツ×コーヒー業態</div>
</div>

<div class="container">

  <div class="grid">
    <div class="card"><div class="label">評価ランク</div><div class="value">{escape(safe(row.get("評価ランク")))}</div></div>
    <div class="card"><div class="label">事業成立性スコア</div><div class="value">{escape(safe(row.get("事業成立性スコア")))}</div></div>
    <div class="card"><div class="label">必要月商</div><div class="value">{yen(monthly_sales)}</div></div>
    <div class="card"><div class="label">推奨必要日客数</div><div class="value">{people(recommended_customers)}</div></div>
    <div class="card"><div class="label">推定席数</div><div class="value">{people(seats)}</div></div>
    <div class="card"><div class="label">初期投資中央値</div><div class="value">{yen(row.get("初期投資中央値"))}</div></div>
  </div>

  <div class="section">
    <h2>1. 物件概要</h2>
    <p><span class="badge">{escape(safe(row.get("掲載サイト")))}</span>
       <span class="badge">{escape(safe(row.get("立地区分")))}</span>
       <span class="badge">{escape(safe(row.get("店舗規模")))}</span>
       <span class="badge">{escape(safe(row.get("階数判定")))}</span>
       <span class="badge">駐車場：{escape(safe(row.get("駐車場判定")))}</span></p>
    <p><b>所在地：</b>{escape(safe(row.get("所在地")))}</p>
    <p><b>家賃：</b>{escape(safe(row.get("家賃")))}（{yen(row.get("家賃_円"))}）</p>
    <p><b>坪数：</b>{escape(safe(row.get("坪数_補正")))} 坪</p>
    <p>{detail_link}</p>
  </div>

  <div class="section">
    <h2>2. 推奨営業モデル</h2>
    <p><b>事業成立パターン：</b>{escape(safe(row.get("事業成立パターン")))}</p>
    <p><b>推奨カフェモデル：</b>{escape(safe(row.get("推奨カフェモデル")))}</p>
    <p><b>商品構成戦略：</b>{escape(strategy)}</p>
    <div class="good">
      この物件では、席数・立地・必要客数をもとに、上記の商品構成を基本案として想定します。
      かき氷は通年損益には含めず、夏季の上振れ商品として別枠で扱います。
    </div>
  </div>

  <div class="section">
    <h2>3. 売上計画</h2>
    <div class="grid">
      <div class="card"><div class="label">必要日商</div><div class="value">{yen(daily_sales)}</div></div>
      <div class="card"><div class="label">理論必要日客数</div><div class="value">{people(theoretical_customers)}</div></div>
      <div class="card"><div class="label">推奨必要日客数</div><div class="value">{people(recommended_customers)}</div></div>
      <div class="card"><div class="label">商品構成上の平均客単価</div><div class="value">{yen(average_price)}</div></div>
    </div>
    <p><b>平日必要客数：</b>{people(weekday_customers)} / <b>休日必要客数：</b>{people(weekend_customers)}</p>
  </div>

  <div class="section">
    <h2>4. メニュー構成</h2>
    <table>
      <thead>
        <tr>
          <th>カテゴリ</th>
          <th>売上構成比</th>
          <th>月間売上目安</th>
          <th>想定単価</th>
        </tr>
      </thead>
      <tbody>
        {menu_rows}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>5. 人員・オペレーション計画</h2>
    <div class="card">
      <div class="label">推奨体制</div>
      <div class="value">{escape(staff_title)}</div>
    </div>
    <p>{escape(staff_comment)}</p>
    <p><b>基本役割分担：</b></p>
    <ul>
      <li>A：注文・会計・受け渡し・コーヒー</li>
      <li>B：フルーツドリンク・パフェ製造・仕込み補充</li>
      <li>C：ピーク時の洗い物・補充・客席リセット</li>
    </ul>
  </div>

  <div class="section">
    <h2>6. 通年損益シミュレーション</h2>
    <table>
      <tr><th>項目</th><th>金額</th></tr>
      <tr><td>必要月商</td><td>{yen(monthly_sales)}</td></tr>
      <tr><td>原価</td><td>{yen(food_cost)}</td></tr>
      <tr><td>人件費</td><td>{yen(labor_cost)}</td></tr>
      <tr><td>家賃</td><td>{yen(rent)}</td></tr>
      <tr><td>その他固定費</td><td>{yen(other_fixed)}</td></tr>
      <tr><td><b>営業利益目安</b></td><td><b>{yen(operating_profit)}</b></td></tr>
    </table>
  </div>

  <div class="section">
    <h2>7. 夏季ブースト：かき氷導入</h2>
    <div class="warn">
      かき氷は通年成立性の計算には含めず、7〜9月の上振れ商品として扱います。
      この物件では、夏季売上の上振れ余地を約 {pct(summer_boost)} と見ます。
    </div>
    <p><b>夏季月商目安：</b>{yen(summer_sales)}</p>
  </div>

  <div class="section">
    <h2>8. 開業判断コメント</h2>
    <p>{escape(safe(row.get("評価コメント")))}</p>
    <p>{escape(safe(row.get("ダッシュボード表示コメント")))}</p>
  </div>

  <p><a href="index.html">一覧へ戻る</a></p>

</div>
</body>
</html>
"""
    return html


def make_index(rows):
    links = []
    for row in rows:
        links.append(f"""
        <tr>
          <td>{escape(safe(row["物件名"]))}</td>
          <td>{escape(safe(row["評価ランク"]))}</td>
          <td>{escape(safe(row["事業成立パターン"]))}</td>
          <td>{yen(row["必要月商"])}</td>
          <td>{people(row["推奨必要日客数"])}</td>
          <td><a href="{escape(row["file_name"])}">営業シミュレーション</a></td>
        </tr>
        """)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>物件別営業シミュレーション一覧</title>
<style>
body {{
  font-family: sans-serif;
  margin: 24px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
}}
th, td {{
  border-bottom: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}}
th {{
  background: #f4f4f4;
}}
a {{
  color: #0066cc;
}}
</style>
</head>
<body>
<h1>物件別営業シミュレーション一覧</h1>
<p>フルーツ×コーヒー業態を前提に、各物件の席数・立地・必要客数から商品構成と運営体制を自動生成した資料です。</p>
<table>
<thead>
<tr>
<th>物件名</th>
<th>評価ランク</th>
<th>事業成立パターン</th>
<th>必要月商</th>
<th>推奨必要日客数</th>
<th>詳細</th>
</tr>
</thead>
<tbody>
{''.join(links)}
</tbody>
</table>
</body>
</html>
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV).fillna("")

    rows = []

    for i, row in df.iterrows():
        file_name = slugify(row.get("物件名"), i + 1)
        out_path = OUT_DIR / file_name

        html = make_html(row, i + 1, file_name)
        out_path.write_text(html, encoding="utf-8")

        r = row.to_dict()
        r["file_name"] = file_name
        rows.append(r)

    INDEX_HTML.write_text(make_index(rows), encoding="utf-8")

    print(f"[LOAD] {INPUT_CSV}: {len(df)}件")
    print(f"[SAVE] {OUT_DIR}")
    print(f"[INDEX] {INDEX_HTML}")


if __name__ == "__main__":
    main()