from pathlib import Path
import html
import re
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DASHBOARD = BASE_DIR / "output" / "archive_csv" / "cafe_business_dashboard.csv"
INPUT_BUSINESS_PLAN = BASE_DIR / "output" / "competitors" / "business_plan_dashboard_with_competitors.csv"
INPUT_COMPETITOR_SUMMARY = BASE_DIR / "output" / "competitors" / "property_competitor_summary.csv"
INPUT_COMPETITORS = BASE_DIR / "data" / "competitors" / "competitors_master.csv"

OUTPUT_DIR = BASE_DIR / "output" / "reports"
OUTPUT_HTML = OUTPUT_DIR / "cafe_business_analysis_report.html"

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


def esc(v):
    if pd.isna(v):
        return ""
    return html.escape(str(v))


def to_number(v):
    if pd.isna(v):
        return None
    s = str(v)
    s = s.replace(",", "")
    s = s.replace("円", "")
    s = s.replace("人", "")
    s = s.replace("坪", "")
    s = s.replace("約", "")
    s = s.strip()
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    return float(m.group())


def yen(n):
    if pd.isna(n):
        return "-"
    return f"{int(round(n)):,}円"


def num(n, suffix=""):
    if pd.isna(n):
        return "-"
    return f"{n:,.1f}{suffix}"


def load_data():
    df = pd.read_csv(INPUT_DASHBOARD)

    if INPUT_BUSINESS_PLAN.exists():
        bp = pd.read_csv(INPUT_BUSINESS_PLAN)
        use_cols = [
            c for c in [
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
            if c in bp.columns
        ]
        if "物件名" in use_cols:
            bp = bp[use_cols].drop_duplicates("物件名")
            dup = [c for c in use_cols if c != "物件名" and c in df.columns]
            if dup:
                df = df.drop(columns=dup)
            df = df.merge(bp, on="物件名", how="left")

    if INPUT_COMPETITOR_SUMMARY.exists():
        summary = pd.read_csv(INPUT_COMPETITOR_SUMMARY)
        use_cols = [
            c for c in [
                "物件名",
                "nearby_500m_count",
                "nearby_1000m_count",
                "nearest_competitor_name",
                "nearest_competitor_distance_m",
            ]
            if c in summary.columns
        ]
        if "物件名" in use_cols:
            summary = summary[use_cols].drop_duplicates("物件名")
            dup = [c for c in use_cols if c != "物件名" and c in df.columns]
            if dup:
                df = df.drop(columns=dup)
            df = df.merge(summary, on="物件名", how="left")

    for col in ["必要月商", "推奨必要日客数", "初期投資中央値", "坪数_補正", "nearby_500m_count", "nearby_1000m_count", "nearest_competitor_distance_m", "seongsu_fit_score"]:
        if col in df.columns:
            df[col + "_num"] = df[col].apply(to_number)

    return df


def load_competitors():
    if not INPUT_COMPETITORS.exists():
        return pd.DataFrame()
    return pd.read_csv(INPUT_COMPETITORS, dtype=str).fillna("")


def q(series, value):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return None
    return float(s.quantile(value))

def to_yen(v):
    if pd.isna(v):
        return None

    s = str(v).strip()

    if not s:
        return None

    if any(word in s for word in ["未定", "相談", "問い合わせ", "要確認"]):
        return None

    n = to_number(s)

    if n is None:
        return None

    if "万円" in s or "万" in s:
        return n * 10000

    return n

def make_pattern_summary(df):
    rows = []
    for pattern, g in df.groupby("事業成立パターン", dropna=False):
        pattern = str(pattern)
        need_sales = g.get("必要月商_num", pd.Series(dtype=float))
        daily_customers = g.get("推奨必要日客数_num", pd.Series(dtype=float))
        rent = g["家賃"].apply(to_yen) if "家賃" in g.columns else pd.Series(dtype=float)

        p25_sales = q(need_sales, 0.25)
        med_sales = q(need_sales, 0.50)
        p75_sales = q(need_sales, 0.75)

        # CSV由来の必要月商に対して、返済・運転資金余力を20%上乗せした水準。
        ideal_sales = p75_sales * 1.2 if p75_sales is not None else None

        rows.append({
            "pattern": pattern,
            "count": len(g),
            "color": PATTERN_COLORS.get(pattern, "#666"),
            "rent_median": q(rent, 0.50),
            "tsubo_median": q(g.get("坪数_補正_num", pd.Series(dtype=float)), 0.50),
            "need_sales_p25": p25_sales,
            "need_sales_median": med_sales,
            "need_sales_p75": p75_sales,
            "ideal_sales": ideal_sales,
            "daily_customers_median": q(daily_customers, 0.50),
            "daily_customers_p75": q(daily_customers, 0.75),
            "nearby_500m_median": q(g.get("nearby_500m_count_num", pd.Series(dtype=float)), 0.50),
            "nearby_1000m_median": q(g.get("nearby_1000m_count_num", pd.Series(dtype=float)), 0.50),
            "seongsu_score_median": q(g.get("seongsu_fit_score_num", pd.Series(dtype=float)), 0.50),
        })

    return sorted(rows, key=lambda x: x["count"], reverse=True)


def make_source_summary(comp):
    if comp.empty or "source" not in comp.columns:
        return {}
    return comp["source"].value_counts().to_dict()


def make_top_properties(df, limit=20):
    score_col = "seongsu_fit_score_num" if "seongsu_fit_score_num" in df.columns else None
    sales_col = "必要月商_num" if "必要月商_num" in df.columns else None

    work = df.copy()
    if score_col:
        work["_sort_score"] = pd.to_numeric(work[score_col], errors="coerce").fillna(0)
    else:
        work["_sort_score"] = 0

    if sales_col:
        work["_sort_sales"] = pd.to_numeric(work[sales_col], errors="coerce").fillna(999999999)
    else:
        work["_sort_sales"] = 999999999

    work = work.sort_values(["_sort_score", "_sort_sales"], ascending=[False, True])
    return work.head(limit)


def render_pattern_cards(rows):
    html_rows = []
    for r in rows:
        html_rows.append(f"""
        <section class="pattern-card" style="--accent:{r['color']}">
          <div class="pattern-head">
            <div>
              <h3>{esc(r['pattern'])}</h3>
              <p>{r['count']}件</p>
            </div>
            <div class="pattern-badge">中央値ベース</div>
          </div>

          <div class="metric-grid">
            <div class="metric"><span>中央値家賃</span><b>{yen(r['rent_median'])}</b></div>
            <div class="metric"><span>中央値坪数</span><b>{num(r['tsubo_median'], "坪")}</b></div>
            <div class="metric"><span>標準必要月商</span><b>{yen(r['need_sales_median'])}</b></div>
            <div class="metric"><span>理想月商</span><b>{yen(r['ideal_sales'])}</b></div>
            <div class="metric"><span>標準必要日客数</span><b>{num(r['daily_customers_median'], "人/日")}</b></div>
            <div class="metric"><span>上位日客数目安</span><b>{num(r['daily_customers_p75'], "人/日")}</b></div>
            <div class="metric"><span>500m競合中央値</span><b>{num(r['nearby_500m_median'], "件")}</b></div>
            <div class="metric"><span>ソンス適性中央値</span><b>{num(r['seongsu_score_median'], "点")}</b></div>
          </div>

          <p class="note">
            理想月商は、同パターン内の必要月商75パーセンタイルに20%の安全余力を加えた水準。
            返済・広告費・人件費変動に耐えるための金融機関説明用ラインとして設定。
          </p>
        </section>
        """)
    return "\n".join(html_rows)


def render_pattern_table(rows):
    trs = []
    for r in rows:
        trs.append(f"""
        <tr>
          <td><span class="dot" style="background:{r['color']}"></span>{esc(r['pattern'])}</td>
          <td>{r['count']}</td>
          <td>{yen(r['rent_median'])}</td>
          <td>{yen(r['need_sales_median'])}</td>
          <td>{yen(r['ideal_sales'])}</td>
          <td>{num(r['daily_customers_median'], "人")}</td>
          <td>{num(r['nearby_500m_median'], "件")}</td>
          <td>{num(r['seongsu_score_median'], "点")}</td>
        </tr>
        """)
    return "\n".join(trs)


def render_top_properties(df):
    trs = []
    for _, r in df.iterrows():
        map_url = f'all_properties_map.html?property={html.escape(str(r.get("物件名", "")))}'
        trs.append(f"""
        <tr>
          <td><a href="{map_url}">{esc(r.get("物件名"))}</a></td>
          <td>{esc(r.get("事業成立パターン"))}</td>
          <td>{esc(r.get("家賃"))}</td>
          <td>{esc(r.get("必要月商"))}</td>
          <td>{esc(r.get("推奨必要日客数"))}</td>
          <td>{esc(r.get("nearby_500m_count"))}</td>
          <td>{esc(r.get("seongsu_fit_score"))}</td>
        </tr>
        """)
    return "\n".join(trs)


def main():
    df = load_data()
    comp = load_competitors()

    pattern_rows = make_pattern_summary(df)
    source_summary = make_source_summary(comp)
    top_properties = make_top_properties(df)

    total_properties = len(df)
    total_competitors = len(comp)
    geocoded = df.dropna(subset=[c for c in ["latitude", "longitude"] if c in df.columns]).shape[0]

    source_cards = ""
    for key, value in source_summary.items():
        source_cards += f'<div class="summary-card"><span>{esc(key)}</span><b>{value}件</b></div>'

    pattern_json = json.dumps([
        {
            "pattern": r["pattern"],
            "count": r["count"],
            "ideal_sales": r["ideal_sales"] or 0,
            "need_sales_median": r["need_sales_median"] or 0,
            "color": r["color"],
        }
        for r in pattern_rows
    ], ensure_ascii=False)

    html_text = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>高松市カフェ開業 事業計画・融資向け分析レポート</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --green:#2f8f2f;
  --bg:#f7f2ea;
  --ink:#221a14;
  --muted:#6f6258;
  --card:#fff;
  --line:#e6d8c8;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);
  color:var(--ink);
}}
.header {{
  background:#fff;
  border-bottom:4px solid var(--green);
  padding:24px 36px;
  position:sticky;
  top:0;
  z-index:10;
}}
.header h1 {{ margin:0; font-size:26px; }}
.header p {{ margin:8px 0 0; color:var(--muted); }}
main {{ padding:28px 36px 56px; max-width:1440px; margin:auto; }}
.section {{ margin:0 0 34px; }}
.section h2 {{ font-size:22px; margin:0 0 14px; }}
.summary-grid {{
  display:grid;
  grid-template-columns:repeat(4,minmax(180px,1fr));
  gap:14px;
}}
.summary-card {{
  background:#fff;
  border:1px solid var(--line);
  border-radius:18px;
  padding:18px;
  box-shadow:0 8px 20px rgba(0,0,0,.05);
}}
.summary-card span {{ display:block; color:var(--muted); font-weight:700; font-size:13px; }}
.summary-card b {{ display:block; margin-top:8px; font-size:28px; }}
.insight {{
  background:#fff;
  border-left:7px solid var(--green);
  border-radius:16px;
  padding:20px 22px;
  line-height:1.85;
  box-shadow:0 8px 20px rgba(0,0,0,.05);
}}
.table-wrap {{
  overflow:auto;
  background:#fff;
  border:1px solid var(--line);
  border-radius:18px;
}}
table {{ width:100%; border-collapse:collapse; min-width:980px; }}
th,td {{ padding:13px 14px; border-bottom:1px solid #eee2d5; text-align:right; }}
th:first-child,td:first-child {{ text-align:left; }}
th {{ background:#fbf8f3; color:#4b4038; font-size:13px; }}
td {{ font-size:14px; }}
.dot {{
  display:inline-block;
  width:11px;
  height:11px;
  border-radius:50%;
  margin-right:8px;
}}
.pattern-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(320px,1fr));
  gap:18px;
}}
.pattern-card {{
  background:#fff;
  border:1px solid var(--line);
  border-top:7px solid var(--accent);
  border-radius:20px;
  padding:20px;
  box-shadow:0 8px 22px rgba(0,0,0,.06);
}}
.pattern-head {{
  display:flex;
  justify-content:space-between;
  gap:14px;
  align-items:flex-start;
}}
.pattern-head h3 {{ margin:0; font-size:19px; }}
.pattern-head p {{ margin:6px 0 0; color:var(--muted); }}
.pattern-badge {{
  background:var(--accent);
  color:#fff;
  border-radius:999px;
  padding:6px 10px;
  font-size:12px;
  font-weight:800;
  white-space:nowrap;
}}
.metric-grid {{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:10px;
  margin-top:18px;
}}
.metric {{
  background:#fbf8f3;
  border:1px solid #eee2d5;
  border-radius:14px;
  padding:11px;
}}
.metric span {{ display:block; color:var(--muted); font-size:11px; font-weight:800; }}
.metric b {{ display:block; margin-top:5px; font-size:15px; }}
.note {{
  margin:14px 0 0;
  color:#5d5149;
  font-size:12px;
  line-height:1.8;
}}
.chart-card {{
  background:#fff;
  border:1px solid var(--line);
  border-radius:18px;
  padding:18px;
}}
.bar {{
  margin:12px 0;
}}
.bar-label {{
  display:flex;
  justify-content:space-between;
  font-size:13px;
  font-weight:800;
}}
.bar-track {{
  height:13px;
  background:#eee4d8;
  border-radius:999px;
  overflow:hidden;
  margin-top:6px;
}}
.bar-fill {{
  height:100%;
  border-radius:999px;
}}
a {{ color:#1d6f1d; font-weight:800; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.footer-note {{
  margin-top:34px;
  color:var(--muted);
  line-height:1.8;
  font-size:13px;
}}
@media(max-width:900px) {{
  main {{ padding:18px; }}
  .header {{ padding:18px; }}
  .summary-grid,.pattern-grid {{ grid-template-columns:1fr; }}
  .metric-grid {{ grid-template-columns:repeat(2,1fr); }}
}}
</style>
</head>
<body>
<header class="header">
  <h1>高松市カフェ開業 事業計画・融資向け分析レポート</h1>
  <p>物件CSV・競合CSV・事業評価CSVを根拠に、売上目標・集客目安・競合環境・ソンス風再現可能性を定量整理。</p>
</header>

<main>
  <section class="section">
    <div class="summary-grid">
      <div class="summary-card"><span>分析対象物件</span><b>{total_properties}件</b></div>
      <div class="summary-card"><span>緯度経度あり物件</span><b>{geocoded}件</b></div>
      <div class="summary-card"><span>競合店舗</span><b>{total_competitors}件</b></div>
      {source_cards}
    </div>
  </section>

  <section class="section">
    <h2>結論</h2>
    <div class="insight">
      本レポートは、取得済みCSVに含まれる「必要月商」「推奨必要日客数」「事業成立パターン」「近隣競合数」「ソンス適性スコア」を用いて、
      カフェ開業候補地を金融機関説明に耐える形で整理したものです。
      目標月商は推測値ではなく、各物件CSV上の必要月商をパターン別に集計し、
      標準水準は中央値、理想水準は75パーセンタイルに20%の安全余力を加えた値として算出しています。
    </div>
  </section>

  <section class="section">
    <h2>事業成立パターン別 売上・集客目安</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>事業成立パターン</th>
            <th>件数</th>
            <th>中央値家賃</th>
            <th>標準必要月商</th>
            <th>理想月商</th>
            <th>必要日客数中央値</th>
            <th>500m競合中央値</th>
            <th>ソンス適性中央値</th>
          </tr>
        </thead>
        <tbody>
          {render_pattern_table(pattern_rows)}
        </tbody>
      </table>
    </div>
  </section>

  <section class="section">
    <h2>パターン別 詳細カード</h2>
    <div class="pattern-grid">
      {render_pattern_cards(pattern_rows)}
    </div>
  </section>

  <section class="section">
    <h2>理想月商 比較</h2>
    <div class="chart-card" id="salesChart"></div>
  </section>

  <section class="section">
    <h2>ソンス風再現可能性の見方</h2>
    <div class="insight">
      ソンス風再現可能性は、単に韓国風内装にできるかではなく、
      「高単価を許容できる立地か」「競合が多すぎず、かつカフェ需要が見込めるか」
      「必要月商に対して日客数が現実的か」を見るための補助指標です。
      ソンス適性スコアが高く、理想月商に対する必要日客数が過大でない物件ほど、
      世界観型・SNS型・高単価型カフェとして金融機関へ説明しやすい候補になります。
    </div>
  </section>

  <section class="section">
    <h2>候補物件ランキング</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>物件名</th>
            <th>事業成立パターン</th>
            <th>家賃</th>
            <th>必要月商</th>
            <th>必要日客数</th>
            <th>500m競合</th>
            <th>ソンス適性</th>
          </tr>
        </thead>
        <tbody>
          {render_top_properties(top_properties)}
        </tbody>
      </table>
    </div>
  </section>

  <div class="footer-note">
    参照CSV：
    {esc(str(INPUT_DASHBOARD.relative_to(BASE_DIR)))},
    {esc(str(INPUT_BUSINESS_PLAN.relative_to(BASE_DIR)))},
    {esc(str(INPUT_COMPETITOR_SUMMARY.relative_to(BASE_DIR)))},
    {esc(str(INPUT_COMPETITORS.relative_to(BASE_DIR)))}。
    本レポートの数値は上記CSVを読み込み、スクリプト実行時点で再計算しています。
  </div>
</main>

<script>
const patternData = {pattern_json};

function yen(v) {{
  if (!v) return "-";
  return Math.round(v).toLocaleString() + "円";
}}

const maxSales = Math.max(...patternData.map(d => d.ideal_sales || 0), 1);
const chart = document.getElementById("salesChart");

patternData.forEach(d => {{
  const width = Math.max(3, (d.ideal_sales / maxSales) * 100);
  const row = document.createElement("div");
  row.className = "bar";
  row.innerHTML = `
    <div class="bar-label">
      <span>${{d.pattern}}</span>
      <span>理想月商：${{yen(d.ideal_sales)}} / 標準：${{yen(d.need_sales_median)}}</span>
    </div>
    <div class="bar-track">
      <div class="bar-fill" style="width:${{width}}%; background:${{d.color}}"></div>
    </div>
  `;
  chart.appendChild(row);
}});
</script>
</body>
</html>
"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html_text, encoding="utf-8")

    print(f"[LOAD] dashboard: {INPUT_DASHBOARD}")
    print(f"[LOAD] business_plan: {INPUT_BUSINESS_PLAN}")
    print(f"[LOAD] competitor_summary: {INPUT_COMPETITOR_SUMMARY}")
    print(f"[LOAD] competitors: {INPUT_COMPETITORS}")
    print(f"[SAVE] {OUTPUT_HTML}")


if __name__ == "__main__":
    main()