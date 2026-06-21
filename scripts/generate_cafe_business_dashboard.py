from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"
OUTPUT_HTML = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.html"


def yen(value):
    if pd.isna(value) or value == "":
        return ""
    try:
        return f"{int(round(float(value))):,}円"
    except Exception:
        return ""


def safe(value):
    if pd.isna(value):
        return ""
    return str(value)


def main():
    df = pd.read_csv(INPUT_CSV).fillna("")

    plot_df = df[
        (df["必要月商"].astype(str).str.strip() != "") &
        (df["必要日客数_26日営業"].astype(str).str.strip() != "")
    ].copy()

    plot_df["必要月商"] = pd.to_numeric(plot_df["必要月商"], errors="coerce")
    plot_df["必要日客数_26日営業"] = pd.to_numeric(
        plot_df["必要日客数_26日営業"],
        errors="coerce"
    )
    plot_df["初期投資中央値"] = pd.to_numeric(
        plot_df["初期投資中央値"],
        errors="coerce"
    )
    plot_df["事業成立性スコア"] = pd.to_numeric(
        plot_df["事業成立性スコア"],
        errors="coerce"
    )

    plot_df = plot_df.dropna(
        subset=["必要月商", "必要日客数_26日営業"]
    )

    points = []

    for _, row in plot_df.iterrows():
        initial_mid = row.get("初期投資中央値", "")
        size = 10

        if pd.notna(initial_mid) and initial_mid != "":
            size = max(8, min(36, float(initial_mid) / 1_000_000))

        points.append({
            "物件名": safe(row.get("物件名")),
            "所在地": safe(row.get("所在地")),
            "掲載サイト": safe(row.get("掲載サイト")),
            "詳細URL": safe(row.get("詳細URL")),
            "家賃": safe(row.get("家賃")),
            "家賃_円": yen(row.get("家賃_円")),
            "坪数_補正": safe(row.get("坪数_補正")),
            "坪単価": yen(row.get("坪単価")),
            "飲食可否": safe(row.get("飲食可否")),
            "立地区分": safe(row.get("立地区分")),
            "店舗規模": safe(row.get("店舗規模")),
            "階数判定": safe(row.get("階数判定")),
            "駐車場判定": safe(row.get("駐車場判定")),
            "事業成立パターン": safe(row.get("事業成立パターン")),
            "不足理由": safe(row.get("不足理由")),
            "推奨カフェモデル": safe(row.get("推奨カフェモデル")),
            "必要月商": float(row.get("必要月商")),
            "必要月商表示": yen(row.get("必要月商")),
            "必要日客数": float(row.get("必要日客数_26日営業")),
            "初期投資中央値": yen(row.get("初期投資中央値")),
            "事業成立性スコア": safe(row.get("事業成立性スコア")),
            "評価ランク": safe(row.get("評価ランク")),
            "評価コメント": safe(row.get("評価コメント")),
            "ダッシュボード表示コメント": safe(row.get("ダッシュボード表示コメント")),
            "marker_size": size,
        })

    table_cols = [
        "評価ランク",
        "事業成立性スコア",
        "事業成立パターン",
        "不足理由",
        "物件名",
        "所在地",
        "家賃",
        "坪数_補正",
        "必要月商",
        "必要日客数_26日営業",
        "初期投資中央値",
        "飲食可否",
        "立地区分",
        "店舗規模",
        "掲載サイト",
        "詳細URL",
    ]

    table_df = df[table_cols].copy()

    for col in ["必要月商", "初期投資中央値"]:
        table_df[col] = pd.to_numeric(table_df[col], errors="coerce").apply(yen)

    table_df["詳細URL"] = table_df["詳細URL"].apply(
        lambda x: f'<a href="{x}" target="_blank">詳細</a>' if str(x).strip() else ""
    )

    html_table = table_df.to_html(
        index=False,
        escape=False,
        table_id="property_table",
        classes="display nowrap",
    )

    points_json = json.dumps(points, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>高松市 カフェ事業性ダッシュボード</title>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>

<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>

<style>
body {{
  font-family: sans-serif;
  margin: 20px;
  color: #222;
}}

h1 {{
  margin-bottom: 8px;
}}

.note {{
  background: #f7f7f7;
  border-left: 5px solid #888;
  padding: 12px 16px;
  margin: 16px 0 24px 0;
  line-height: 1.7;
}}

.summary {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}}

.card {{
  background: #ffffff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 160px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}

.card .label {{
  color: #666;
  font-size: 13px;
}}

.card .value {{
  font-size: 24px;
  font-weight: bold;
  margin-top: 4px;
}}

#chart {{
  width: 100%;
  height: 680px;
  border: 1px solid #ddd;
  border-radius: 8px;
}}

#detail {{
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fcfcfc;
  line-height: 1.7;
}}

#detail h2 {{
  margin-top: 0;
}}

table {{
  width: 100%;
}}

.section-title {{
  margin-top: 32px;
  border-bottom: 2px solid #ddd;
  padding-bottom: 8px;
}}

a {{
  color: #0066cc;
}}

.badge {{
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  background: #eee;
  margin-right: 4px;
  font-size: 12px;
}}
</style>
</head>

<body>
<h1>高松市 カフェ事業性ダッシュボード</h1>

<div class="note">
  <div>このダッシュボードは、統合済み216件の店舗・事業用賃貸物件をもとに、カフェ開業時の事業成立性を可視化したものです。</div>
  <div>横軸は必要月商、縦軸は必要日客数です。左下に近いほど少ない売上・少ない客数で成立しやすい物件です。</div>
  <div>点の色は事業成立パターン、点の大きさは初期投資規模の目安です。点をクリックすると物件詳細を表示します。</div>
</div>

<div class="summary">
  <div class="card">
    <div class="label">全物件</div>
    <div class="value">{len(df)}</div>
  </div>
  <div class="card">
    <div class="label">評価対象</div>
    <div class="value">{len(plot_df)}</div>
  </div>
  <div class="card">
    <div class="label">要確認</div>
    <div class="value">{len(df) - len(plot_df)}</div>
  </div>
</div>

<div id="chart"></div>

<div id="detail">
  <h2>物件詳細</h2>
  <p>散布図上の点をクリックすると、ここに物件情報が表示されます。</p>
</div>

<h2 class="section-title">物件一覧</h2>
{html_table}

<script>
const points = {points_json};

const patterns = [...new Set(points.map(p => p["事業成立パターン"]))];

const traces = patterns.map(pattern => {{
  const rows = points.filter(p => p["事業成立パターン"] === pattern);

  return {{
    type: "scatter",
    mode: "markers",
    name: pattern,
    x: rows.map(p => p["必要月商"]),
    y: rows.map(p => p["必要日客数"]),
    text: rows.map(p => p["物件名"]),
    customdata: rows,
    marker: {{
      size: rows.map(p => p["marker_size"]),
      opacity: 0.75,
      line: {{
        width: 1,
        color: "#333"
      }}
    }},
    hovertemplate:
        "<b>%{{text}}</b><br>" +
        "事業成立パターン: " + pattern + "<br>" +
        "必要月商: %{{x:,.0f}}円<br>" +
        "必要日客数: %{{y:.0f}}人<br>" +
        "<extra></extra>"
  }};
}});

const layout = {{
  title: "必要月商 × 必要日客数",
  xaxis: {{
    title: "必要月商（円）",
    tickformat: ",",
    zeroline: false
  }},
  yaxis: {{
    title: "必要日客数（26日営業）",
    zeroline: false
  }},
  legend: {{
    orientation: "h",
    y: -0.2
  }},
  margin: {{
    l: 80,
    r: 40,
    t: 60,
    b: 120
  }},
  hovermode: "closest"
}};

Plotly.newPlot("chart", traces, layout, {{
  responsive: true,
  displayModeBar: true
}});

document.getElementById("chart").on("plotly_click", function(data) {{
  const p = data.points[0].customdata;

  const urlHtml = p["詳細URL"]
    ? `<a href="${{p["詳細URL"]}}" target="_blank">詳細ページを開く</a>`
    : "詳細URLなし";

  document.getElementById("detail").innerHTML = `
    <h2>${{p["物件名"]}}</h2>
    <div>
      <span class="badge">${{p["評価ランク"]}}</span>
      <span class="badge">${{p["事業成立パターン"]}}</span>
      <span class="badge">${{p["立地区分"]}}</span>
      <span class="badge">${{p["店舗規模"]}}</span>
    </div>
    <p><b>所在地：</b>${{p["所在地"]}}</p>
    <p><b>掲載サイト：</b>${{p["掲載サイト"]}}</p>
    <p><b>家賃：</b>${{p["家賃"]}}（${{p["家賃_円"]}}）</p>
    <p><b>坪数：</b>${{p["坪数_補正"]}} 坪</p>
    <p><b>坪単価：</b>${{p["坪単価"]}}</p>
    <p><b>飲食可否：</b>${{p["飲食可否"]}}</p>
    <p><b>階数：</b>${{p["階数判定"]}} / <b>駐車場：</b>${{p["駐車場判定"]}}</p>
    <p><b>推奨モデル：</b>${{p["推奨カフェモデル"]}}</p>
    <p><b>必要月商：</b>${{p["必要月商表示"]}}</p>
    <p><b>必要日客数：</b>${{p["必要日客数"]}} 人</p>
    <p><b>初期投資中央値：</b>${{p["初期投資中央値"]}}</p>
    <p><b>評価コメント：</b>${{p["評価コメント"]}}</p>
    <p><b>表示コメント：</b>${{p["ダッシュボード表示コメント"]}}</p>
    <p>${{urlHtml}}</p>
  `;
}});

$(document).ready(function() {{
  $('#property_table').DataTable({{
    pageLength: 25,
    order: [[1, 'desc']],
    scrollX: true,
    initComplete: function () {{
      this.api().columns([0, 2, 3, 11, 12, 13, 14]).every(function () {{
        const column = this;
        const select = $('<select><option value="">すべて</option></select>')
          .appendTo($(column.header()))
          .on('change', function () {{
            const val = $.fn.dataTable.util.escapeRegex($(this).val());
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

    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"[LOAD] {INPUT_CSV}: {len(df)}件")
    print(f"[PLOT] 評価対象: {len(plot_df)}件")
    print(f"[SAVE] {OUTPUT_HTML}")


if __name__ == "__main__":
    main()