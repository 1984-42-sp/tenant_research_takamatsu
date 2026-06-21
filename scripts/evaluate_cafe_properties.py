from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"

INPUT_CSV = OUTPUT_DIR / "all_properties" / "all_properties.csv"
OUTPUT_CSV = OUTPUT_DIR / "all_properties" / "cafe_property_evaluation.csv"
OUTPUT_HTML = OUTPUT_DIR / "all_properties" / "cafe_property_evaluation.html"


CENTER_KEYWORDS = [
    "瓦町", "丸亀町", "南新町", "兵庫町", "片原町", "常磐町",
    "古馬場町", "御坊町", "今新町", "百間町", "鍛冶屋町",
    "亀井町", "田町", "内町", "塩屋町", "福田町"
]

SEMI_CENTER_KEYWORDS = [
    "栗林", "花園", "松島", "松縄", "木太町", "上福岡町",
    "藤塚町", "桜町", "昭和町", "番町", "宮脇町", "西宝町",
    "伏石町", "今里町", "上天神町", "太田", "三条"
]

SUBURB_KEYWORDS = [
    "郷東町", "香西", "鬼無", "国分寺", "牟礼", "庵治",
    "香川町", "仏生山", "川島", "十川", "由良", "円座",
    "一宮", "多肥", "林町", "春日町", "屋島", "高松町"
]


def to_float(value):
    if pd.isna(value):
        return None
    text = str(value).replace(",", "")
    m = re.search(r"[\d.]+", text)
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def classify_location(address):
    text = str(address)

    if any(k in text for k in CENTER_KEYWORDS):
        return "中心街"

    if any(k in text for k in SEMI_CENTER_KEYWORDS):
        return "準中心街"

    if any(k in text for k in SUBURB_KEYWORDS):
        return "郊外"

    return "不明"


def classify_size(tsubo):
    if pd.isna(tsubo):
        return "不明"

    if tsubo <= 12:
        return "極小"
    if tsubo <= 20:
        return "小規模"
    if tsubo <= 35:
        return "中規模"
    return "大型"


def estimate_seats(tsubo, size_class):
    if pd.isna(tsubo):
        return None

    if size_class == "極小":
        return max(4, round(tsubo * 0.8))
    if size_class == "小規模":
        return round(tsubo * 1.1)
    if size_class == "中規模":
        return round(tsubo * 1.3)
    if size_class == "大型":
        return round(tsubo * 1.5)

    return None


def judge_property_type(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))

    if any(k in text for k in ["倉庫", "工場"]):
        return "倉庫・工場系"

    if any(k in text for k in ["店舗", "テナント", "店舗事務所"]):
        return "店舗系"

    if any(k in text for k in ["事務所", "オフィス"]):
        return "事務所系"

    return "不明"


def judge_floor(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))

    if any(k in text for k in ["1F", "1階", "一階", "路面"]):
        return "1階・路面想定"

    if any(k in text for k in ["2F", "2階", "3F", "3階", "4F", "4階", "地下"]):
        return "上階・地下想定"

    return "不明"


def judge_parking(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))

    if any(k in text for k in ["駐車場有", "駐車場あり", "駐車", "P有"]):
        return "あり"

    if any(k in text for k in ["駐車場無", "駐車場なし", "駐車なし"]):
        return "なし"

    return "不明"


def choose_cafe_model(location_class, size_class, property_type, parking):
    if size_class in ["極小", "小規模"] and location_class in ["中心街", "準中心街"]:
        return "小規模ソンス風カフェ・テイクアウト併設"

    if size_class == "中規模" and location_class in ["中心街", "準中心街"]:
        return "回転＋滞在ハイブリッド型カフェ"

    if location_class == "郊外" and size_class in ["中規模", "大型"]:
        if property_type == "倉庫・工場系":
            return "郊外倉庫リノベ型ソンス風カフェ"
        return "郊外滞在型カフェ"

    if size_class == "大型":
        return "大型滞在型カフェ"

    return "要個別検討"


def set_cost_rates(model, size_class):
    if "テイクアウト" in model:
        return 0.26, 0.22, 0.10, 900

    if "ハイブリッド" in model:
        return 0.30, 0.25, 0.10, 1050

    if "倉庫リノベ" in model:
        return 0.32, 0.28, 0.10, 1150

    if "郊外滞在型" in model:
        return 0.32, 0.27, 0.10, 1100

    if "大型" in model:
        return 0.33, 0.28, 0.10, 1150

    return 0.30, 0.25, 0.10, 1000


def estimate_other_fixed_cost(rent, size_class):
    if pd.isna(rent):
        return None

    if size_class == "極小":
        return max(80000, rent * 0.45)

    if size_class == "小規模":
        return max(100000, rent * 0.45)

    if size_class == "中規模":
        return max(160000, rent * 0.50)

    if size_class == "大型":
        return max(250000, rent * 0.55)

    return max(120000, rent * 0.45)


def estimate_initial_investment(tsubo, property_type, model):
    if pd.isna(tsubo):
        return None, None

    if property_type == "倉庫・工場系":
        low_per_tsubo = 350000
        high_per_tsubo = 800000
    elif "テイクアウト" in model:
        low_per_tsubo = 250000
        high_per_tsubo = 600000
    elif "郊外" in model or "大型" in model:
        low_per_tsubo = 300000
        high_per_tsubo = 750000
    else:
        low_per_tsubo = 300000
        high_per_tsubo = 700000

    return round(tsubo * low_per_tsubo), round(tsubo * high_per_tsubo)


def score_property(row):
    score = 0
    comments = []

    if row["飲食可否"] == "可":
        score += 25
        comments.append("飲食可")
    elif row["飲食可否"] == "不明":
        score += 8
        comments.append("飲食可否確認必要")
    else:
        score -= 30
        comments.append("飲食不可の可能性")

    if row["立地区分"] == "中心街":
        score += 18
        comments.append("中心街")
    elif row["立地区分"] == "準中心街":
        score += 14
        comments.append("準中心街")
    elif row["立地区分"] == "郊外":
        score += 10
        comments.append("郊外")

    if row["店舗規模"] in ["小規模", "中規模"]:
        score += 18
        comments.append("カフェ向き規模")
    elif row["店舗規模"] == "大型":
        score += 8
        comments.append("大型で投資負担大")
    elif row["店舗規模"] == "極小":
        score += 6
        comments.append("極小で業態制限あり")

    if row["階数判定"] == "1階・路面想定":
        score += 15
        comments.append("1階・路面想定")
    elif row["階数判定"] == "上階・地下想定":
        score -= 8
        comments.append("上階・地下で集客難度上昇")

    if row["駐車場判定"] == "あり":
        score += 10
        comments.append("駐車場あり")
    elif row["駐車場判定"] == "なし":
        score -= 5
        comments.append("駐車場なし")

    if pd.notna(row["坪単価"]):
        if row["立地区分"] == "中心街" and row["坪単価"] <= 15000:
            score += 8
            comments.append("中心街として坪単価妥当")
        elif row["立地区分"] == "準中心街" and row["坪単価"] <= 10000:
            score += 8
            comments.append("準中心街として坪単価妥当")
        elif row["立地区分"] == "郊外" and row["坪単価"] <= 7000:
            score += 8
            comments.append("郊外として坪単価妥当")
        elif row["坪単価"] >= 18000:
            score -= 8
            comments.append("坪単価高め")

    if score >= 70:
        rank = "A"
    elif score >= 50:
        rank = "B"
    elif score >= 30:
        rank = "C"
    else:
        rank = "D"

    return score, rank, " / ".join(comments)


def yen(value):
    if pd.isna(value):
        return ""
    return f"{int(round(value)):,}"


def main():
    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    rows = []

    for _, row in df.iterrows():
        item = row.to_dict()

        rent = to_float(row.get("家賃数値", "")) or to_float(row.get("家賃", ""))
        area = to_float(row.get("面積数値", "")) or to_float(row.get("面積", ""))
        tsubo = to_float(row.get("坪数数値", "")) or to_float(row.get("坪数", ""))

        if tsubo is None and area is not None:
            tsubo = area / 3.305785

        location_class = classify_location(row.get("所在地", ""))
        size_class = classify_size(tsubo)
        property_type = judge_property_type(row)
        floor = judge_floor(row)
        parking = judge_parking(row)

        tsubo_unit_price = rent / tsubo if rent and tsubo else None

        model = choose_cafe_model(
            location_class=location_class,
            size_class=size_class,
            property_type=property_type,
            parking=parking,
        )

        cost_rate, labor_rate, profit_rate, average_spend = set_cost_rates(model, size_class)

        other_fixed = estimate_other_fixed_cost(rent, size_class) if rent else None
        monthly_fixed = rent + other_fixed if rent and other_fixed else None

        denominator = 1 - cost_rate - labor_rate - profit_rate
        required_monthly_sales = monthly_fixed / denominator if monthly_fixed and denominator > 0 else None
        required_daily_sales = required_monthly_sales / 26 if required_monthly_sales else None

        required_monthly_customers = required_monthly_sales / average_spend if required_monthly_sales else None
        required_daily_customers = required_monthly_customers / 26 if required_monthly_customers else None

        seats = estimate_seats(tsubo, size_class)

        initial_low, initial_high = estimate_initial_investment(tsubo, property_type, model)

        item["立地区分"] = location_class
        item["店舗規模"] = size_class
        item["物件タイプ推定"] = property_type
        item["階数判定"] = floor
        item["駐車場判定"] = parking
        item["坪単価"] = round(tsubo_unit_price) if tsubo_unit_price else None
        item["推奨カフェモデル"] = model
        item["推定席数"] = seats
        item["原価率"] = cost_rate
        item["人件費率"] = labor_rate
        item["利益率"] = profit_rate
        item["想定客単価"] = average_spend
        item["その他固定費"] = round(other_fixed) if other_fixed else None
        item["月間固定費"] = round(monthly_fixed) if monthly_fixed else None
        item["必要月商"] = round(required_monthly_sales) if required_monthly_sales else None
        item["必要日商_26日営業"] = round(required_daily_sales) if required_daily_sales else None
        item["必要月間客数"] = round(required_monthly_customers) if required_monthly_customers else None
        item["必要日客数_26日営業"] = round(required_daily_customers) if required_daily_customers else None
        item["初期投資下限"] = initial_low
        item["初期投資上限"] = initial_high

        score, rank, comment = score_property(item)
        item["評価点"] = score
        item["評価ランク"] = rank
        item["評価コメント"] = comment

        rows.append(item)

    out_df = pd.DataFrame(rows)

    out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    display_cols = [
        "評価ランク",
        "評価点",
        "物件名",
        "所在地",
        "家賃",
        "坪数",
        "坪単価",
        "飲食可否",
        "立地区分",
        "店舗規模",
        "物件タイプ推定",
        "階数判定",
        "駐車場判定",
        "推奨カフェモデル",
        "推定席数",
        "月間固定費",
        "必要月商",
        "必要日商_26日営業",
        "必要日客数_26日営業",
        "初期投資下限",
        "初期投資上限",
        "掲載サイト",
        "詳細URL",
        "評価コメント",
    ]

    html_table = out_df[display_cols].to_html(
        index=False,
        escape=False,
        table_id="cafe_properties",
        classes="display nowrap",
    )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>カフェ開業向け物件評価一覧</title>
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
.note {{
  background: #f7f7f7;
  padding: 12px;
  border-left: 4px solid #999;
  margin-bottom: 20px;
}}
</style>
</head>
<body>
<h1>カフェ開業向け物件評価一覧</h1>

<div class="note">
<p>この一覧は、統合済み物件CSVをもとにした概算評価です。</p>
<p>家賃・坪数・飲食可否・所在地・階数・駐車場・物件種別から、ソンス風カフェ開業向けに概算の必要売上・必要客数・初期投資レンジを算出しています。</p>
</div>

{html_table}

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready(function() {{
  $('#cafe_properties').DataTable({{
    pageLength: 25,
    order: [[1, 'desc']],
    columnDefs: [
      {{
        targets: 22,
        render: function(data, type, row) {{
          if (!data) return "";
          return '<a href="' + data + '" target="_blank">詳細</a>';
        }}
      }}
    ],
    initComplete: function () {{
      this.api().columns([0, 7, 8, 9, 10, 11, 12, 13, 21]).every(function () {{
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

    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"[LOAD] {INPUT_CSV}: {len(df)}件")
    print(f"[SAVE] {OUTPUT_CSV}: {len(out_df)}件")
    print(f"[SAVE] {OUTPUT_HTML}")

    print("[RANK]")
    print(out_df["評価ランク"].value_counts().sort_index())


if __name__ == "__main__":
    main()