from ast import pattern
from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"

INPUT_CSV = OUTPUT_DIR / "all_properties" / "all_properties.csv"
OUTPUT_CSV = OUTPUT_DIR / "all_properties" / "cafe_property_evaluation.csv"
OUTPUT_HTML = OUTPUT_DIR / "all_properties" / "cafe_property_evaluation.html"
DASHBOARD_CSV = OUTPUT_DIR / "all_properties" / "cafe_business_dashboard.csv"
DASHBOARD_HTML = OUTPUT_DIR / "all_properties" / "cafe_business_dashboard.html"


CENTER_KEYWORDS = [
    "瓦町", "丸亀町", "南新町", "兵庫町", "片原町", "常磐町",
    "古馬場町", "御坊町", "今新町", "百間町", "鍛冶屋町",
    "亀井町", "田町", "内町", "塩屋町", "福田町", "大工町"
]

SEMI_CENTER_KEYWORDS = [
    "栗林", "花園", "松島", "松縄", "木太町", "上福岡町",
    "藤塚町", "桜町", "昭和町", "番町", "宮脇町", "西宝町",
    "伏石町", "今里町", "上天神町", "太田", "三条", "中央町",
    "扇町", "上之町", "松福町"
]

SUBURB_KEYWORDS = [
    "郷東町", "香西", "鬼無", "国分寺", "牟礼", "庵治",
    "香川町", "仏生山", "川島", "十川", "由良", "円座",
    "一宮", "多肥", "林町", "春日町", "屋島", "高松町",
    "檀紙町", "西山崎町", "飯田町", "新田町", "香南町", 
    "六条町","東山崎町"
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().replace(",", "")


def first_number(value):
    text = clean_text(value)
    m = re.search(r"\d+(?:\.\d+)?", text)
    if not m:
        return None
    return float(m.group())


def extract_rent_yen(raw_rent, numeric_rent=None):
    """家賃を円単位に正規化する。万円表記を最優先で補正する。"""
    text = clean_text(raw_rent)
    num = first_number(text)

    if num is None:
        num = first_number(numeric_rent)

    if num is None:
        return None

    if any(k in text for k in ["未定", "相談", "応相談"]):
        return None

    if "万円" in text or "万" in text:
        return round(num * 10000)

    # 統合CSVの家賃数値は「万円」から最初の数値だけ取られているケースが多い。
    # raw_rentが空でnumericだけある場合も、1000未満なら万円として扱う。
    if num < 1000:
        return round(num * 10000)

    return round(num)


def extract_area_sqm(raw_area, numeric_area=None):
    text = clean_text(raw_area).replace("ｍ", "m").replace("㎡", "m2")
    num = first_number(text)

    if num is not None and ("m2" in text or "m 2" in text or "平米" in text):
        return num

    num2 = first_number(numeric_area)
    if num2 is not None:
        return num2

    return num


def extract_tsubo(raw_tsubo, raw_area=None, numeric_tsubo=None, area_sqm=None):
    """坪数を抽出する。面積欄の括弧内『(68.37坪)』を優先する。"""
    texts = [clean_text(raw_tsubo), clean_text(raw_area)]

    for text in texts:
        if not text:
            continue
        m = re.search(r"(\d+(?:\.\d+)?)\s*坪", text)
        if m:
            return float(m.group(1))

    num = first_number(numeric_tsubo)
    if num is not None:
        return num

    if area_sqm is not None:
        return area_sqm / 3.305785

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
    if tsubo is None or pd.isna(tsubo):
        return "不明"
    if tsubo <= 12:
        return "極小"
    if tsubo <= 20:
        return "小規模"
    if tsubo <= 35:
        return "中規模"
    return "大型"


def estimate_seats(tsubo, size_class, pattern):
    if tsubo is None or pd.isna(tsubo):
        return None
    if "高回転" in pattern or "小商圏" in pattern:
        return max(4, round(tsubo * 0.9))
    if "高単価" in pattern:
        return max(6, round(tsubo * 0.75))
    if "郊外" in pattern:
        return round(tsubo * 1.1)
    if "大型" in pattern:
        return round(tsubo * 1.2)
    return round(tsubo * 1.0)


def judge_property_type(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))
    if any(k in text for k in ["倉庫", "工場"]):
        return "倉庫・工場系"
    if any(k in text for k in ["店舗", "テナント", "店舗事務所", "貸店舗"]):
        return "店舗系"
    if any(k in text for k in ["事務所", "オフィス"]):
        return "事務所系"
    return "不明"


def judge_floor(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))
    if any(k in text for k in ["1F", "１F", "1階", "１階", "一階", "路面"]):
        return "1階・路面想定"
    if any(k in text for k in ["2F", "２F", "2階", "２階", "3F", "３F", "3階", "３階", "4F", "４F", "4階", "４階", "地下"]):
        return "上階・地下想定"
    return "不明"


def judge_parking(row):
    text = " ".join(str(v) for v in row.values if pd.notna(v))
    if any(k in text for k in ["駐車場有", "駐車場あり", "駐車", "P有", "Ｐ有"]):
        return "あり"
    if any(k in text for k in ["駐車場無", "駐車場なし", "駐車なし"]):
        return "なし"
    return "不明"


def choose_business_pattern(location_class, size_class, parking, rent_yen, tsubo, required_monthly_sales, required_daily_customers, initial_high):
    if rent_yen is None and tsubo is None:
        return "家賃・面積不明型"

    if rent_yen is None:
        return "家賃未定・問い合わせ必要型"

    if tsubo is None:
        return "面積不明・詳細確認型"

    if required_monthly_sales is None or required_daily_customers is None:
        return "要確認・情報不足型"

    if tsubo >= 60 or (initial_high and initial_high >= 30000000) or required_monthly_sales >= 6000000:
        return "大型投資・高売上必須型"

    if location_class == "中心街":
        if size_class in ["極小", "小規模"]:
            return "中心街・高単価型"
        if required_daily_customers >= 60 or rent_yen >= 250000:
            return "中心街・高回転型"
        return "中心街・高単価型"

    if location_class == "準中心街":
        if size_class in ["極小", "小規模"] and required_monthly_sales <= 1200000:
            return "低固定費・小商圏型"
        if required_daily_customers >= 60 or rent_yen >= 250000:
            return "中心街・高回転型"
        return "中心街・高単価型"

    if location_class == "郊外":
        if parking == "あり" or size_class in ["中規模", "大型"]:
            return "郊外・駐車場依存型"
        if required_monthly_sales <= 1200000 and required_daily_customers <= 45:
            return "低固定費・小商圏型"
        return "郊外・駐車場依存型"

    if required_monthly_sales <= 1200000 and required_daily_customers <= 45:
        return "低固定費・小商圏型"

    return "要確認・情報不足型"


def choose_cafe_model(pattern, property_type):
    if pattern == "低固定費・小商圏型":
        return "小規模カフェ・テイクアウト併設"
    if pattern == "中心街・高回転型":
        return "中心街高回転型カフェ"
    if pattern == "中心街・高単価型":
        return "中心街高単価・目的来店型カフェ"
    if pattern == "郊外・駐車場依存型":
        if property_type == "倉庫・工場系":
            return "郊外倉庫リノベ型カフェ"
        return "郊外滞在・ランチ需要型カフェ"
    if pattern == "大型投資・高売上必須型":
        return "大型滞在・複合目的型カフェ"
    return "要個別検討"


def set_cost_rates(pattern):
    if pattern == "低固定費・小商圏型":
        return 0.28, 0.23, 0.10, 900
    if pattern == "中心街・高回転型":
        return 0.30, 0.25, 0.10, 1000
    if pattern == "中心街・高単価型":
        return 0.32, 0.26, 0.10, 1300
    if pattern == "郊外・駐車場依存型":
        return 0.32, 0.27, 0.10, 1100
    if pattern == "大型投資・高売上必須型":
        return 0.33, 0.28, 0.10, 1150
    return 0.30, 0.25, 0.10, 1000


def estimate_other_fixed_cost(rent_yen, size_class):
    if rent_yen is None or pd.isna(rent_yen):
        return None
    if size_class == "極小":
        return max(80000, rent_yen * 0.45)
    if size_class == "小規模":
        return max(100000, rent_yen * 0.45)
    if size_class == "中規模":
        return max(160000, rent_yen * 0.50)
    if size_class == "大型":
        return max(250000, rent_yen * 0.55)
    return max(120000, rent_yen * 0.45)


def estimate_initial_investment(tsubo, property_type, pattern):
    if tsubo is None or pd.isna(tsubo):
        return None, None, None
    if property_type == "倉庫・工場系":
        low, high = 350000, 800000
    elif pattern == "低固定費・小商圏型":
        low, high = 250000, 600000
    elif pattern in ["郊外・駐車場依存型", "大型投資・高売上必須型"]:
        low, high = 300000, 750000
    else:
        low, high = 300000, 700000
    low_total = round(tsubo * low)
    high_total = round(tsubo * high)
    return low_total, high_total, round((low_total + high_total) / 2)


def calc_business_numbers(rent_yen, tsubo, size_class, pattern):
    cost_rate, labor_rate, profit_rate, average_spend = set_cost_rates(pattern)
    other_fixed = estimate_other_fixed_cost(rent_yen, size_class) if rent_yen else None
    monthly_fixed = rent_yen + other_fixed if rent_yen and other_fixed else None
    denominator = 1 - cost_rate - labor_rate - profit_rate
    required_monthly_sales = monthly_fixed / denominator if monthly_fixed and denominator > 0 else None
    required_daily_sales = required_monthly_sales / 26 if required_monthly_sales else None
    required_monthly_customers = required_monthly_sales / average_spend if required_monthly_sales else None
    required_daily_customers = required_monthly_customers / 26 if required_monthly_customers else None
    return {
        "原価率": cost_rate,
        "人件費率": labor_rate,
        "利益率": profit_rate,
        "想定客単価": average_spend,
        "その他固定費": round(other_fixed) if other_fixed else None,
        "月間固定費": round(monthly_fixed) if monthly_fixed else None,
        "必要月商": round(required_monthly_sales) if required_monthly_sales else None,
        "必要日商_26日営業": round(required_daily_sales) if required_daily_sales else None,
        "必要月間客数": round(required_monthly_customers) if required_monthly_customers else None,
        "必要日客数_26日営業": round(required_daily_customers) if required_daily_customers else None,
    }


def score_business(row):
    if row["事業成立パターン"] == "要確認・情報不足型":
        return 0, "要確認", "家賃または坪数が不足しており、事業性算定不可"

    score = 0
    comments = []

    monthly_sales = row.get("必要月商")
    daily_customers = row.get("必要日客数_26日営業")
    initial_mid = row.get("初期投資中央値")

    if monthly_sales is None or daily_customers is None:
        return 0, "要確認", "必要月商または必要客数が算定不可"

    # 必要月商：最重要
    if monthly_sales <= 800000:
        score += 35
        comments.append("必要月商80万円以下")
    elif monthly_sales <= 1500000:
        score += 25
        comments.append("必要月商150万円以下")
    elif monthly_sales <= 2500000:
        score += 15
        comments.append("必要月商250万円以下")
    elif monthly_sales <= 4000000:
        score += 5
        comments.append("必要月商400万円以下")
    else:
        score -= 10
        comments.append("高売上必須")

    # 必要日客数：実現可能性
    if daily_customers <= 35:
        score += 30
        comments.append("必要日客数35人以下")
    elif daily_customers <= 60:
        score += 20
        comments.append("必要日客数60人以下")
    elif daily_customers <= 90:
        score += 10
        comments.append("必要日客数90人以下")
    else:
        score -= 10
        comments.append("多客数が必須")

    # 初期投資
    if initial_mid is not None:
        if initial_mid <= 8000000:
            score += 20
            comments.append("初期投資800万円以下")
        elif initial_mid <= 15000000:
            score += 10
            comments.append("初期投資1500万円以下")
        elif initial_mid <= 25000000:
            score += 0
            comments.append("初期投資は重め")
        else:
            score -= 10
            comments.append("初期投資が重い")

    # 飲食可否
    if row.get("飲食可否") == "可":
        score += 10
        comments.append("飲食可")
    elif row.get("飲食可否") == "不明":
        score -= 5
        comments.append("飲食可否確認必要")
    else:
        score -= 30
        comments.append("飲食不可の可能性")

    # 階数
    if row.get("階数判定") == "1階・路面想定":
        score += 8
        comments.append("1階・路面想定")
    elif row.get("階数判定") == "上階・地下想定":
        score -= 8
        comments.append("上階・地下で集客難度あり")

    # 郊外は駐車場が重要
    if row.get("立地区分") == "郊外":
        if row.get("駐車場判定") == "あり":
            score += 10
            comments.append("郊外で駐車場あり")
        elif row.get("駐車場判定") == "不明":
            score -= 5
            comments.append("郊外で駐車場確認必要")

    # パターン別の補正
    pattern = row.get("事業成立パターン")

    if pattern == "大型投資・高売上必須型":
        score -= 10
        comments.append("大型投資型のため慎重判断")

    if pattern == "中心街・高回転型" and daily_customers > 80:
        score -= 10
        comments.append("中心街でも回転数ハードル高め")

    if pattern == "中心街・高単価型" and row.get("店舗規模") in ["極小", "小規模"]:
        score += 5
        comments.append("小規模高単価モデル向き")

    score = max(0, min(100, round(score)))

    if score >= 85:
        rank = "A"
    elif score >= 70:
        rank = "B"
    elif score >= 50:
        rank = "C"
    else:
        rank = "D"

    return score, rank, " / ".join(comments)


def make_dashboard_comment(row):
    pattern = row.get("事業成立パターン", "")
    if pattern == "要確認・情報不足型":
        return "家賃または坪数が不足。詳細ページで賃料・面積・飲食可否の確認が必要。"
    return f"{pattern}。必要月商{yen(row.get('必要月商'))}円、必要日客数{row.get('必要日客数_26日営業') or ''}人が目安。"


def yen(value):
    if value is None or pd.isna(value) or value == "":
        return ""
    return f"{int(round(float(value))):,}"


def main():
    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")
    rows = []

    for _, row in df.iterrows():
        item = row.to_dict()

        rent_yen = extract_rent_yen(row.get("家賃", ""), row.get("家賃数値", ""))
        area_sqm = extract_area_sqm(row.get("面積", ""), row.get("面積数値", ""))
        tsubo = extract_tsubo(row.get("坪数", ""), row.get("面積", ""), row.get("坪数数値", ""), area_sqm)

        location_class = classify_location(row.get("所在地", ""))
        size_class = classify_size(tsubo)
        property_type = judge_property_type(row)
        floor = judge_floor(row)
        parking = judge_parking(row)
        tsubo_unit_price = rent_yen / tsubo if rent_yen and tsubo else None

        # 事業成立パターン判定前の仮計算。未分類時は標準率で概算する。
        provisional_pattern = "要確認・情報不足型"
        provisional = calc_business_numbers(rent_yen, tsubo, size_class, provisional_pattern)
        initial_low, initial_high, initial_mid = estimate_initial_investment(tsubo, property_type, provisional_pattern)

        pattern = choose_business_pattern(
            location_class=location_class,
            size_class=size_class,
            parking=parking,
            rent_yen=rent_yen,
            tsubo=tsubo,
            required_monthly_sales=provisional["必要月商"],
            required_daily_customers=provisional["必要日客数_26日営業"],
            initial_high=initial_high,
        )

        if rent_yen is None and tsubo is None:
            missing_reason = "家賃・面積不明"
        elif rent_yen is None:
            missing_reason = "家賃未定"
        elif tsubo is None:
            missing_reason = "面積不明"
        elif pattern == "要確認・情報不足型":
            missing_reason = "算定条件不足"
        else:
            missing_reason = ""
        
        business = calc_business_numbers(rent_yen, tsubo, size_class, pattern)
        initial_low, initial_high, initial_mid = estimate_initial_investment(tsubo, property_type, pattern)
        seats = estimate_seats(tsubo, size_class, pattern)
        model = choose_cafe_model(pattern, property_type)

        item["家賃_円"] = rent_yen
        item["面積_㎡_補正"] = round(area_sqm, 2) if area_sqm else None
        item["坪数_補正"] = round(tsubo, 2) if tsubo else None
        item["立地区分"] = location_class
        item["店舗規模"] = size_class
        item["物件タイプ推定"] = property_type
        item["階数判定"] = floor
        item["駐車場判定"] = parking
        item["坪単価"] = round(tsubo_unit_price) if tsubo_unit_price else None
        item["事業成立パターン"] = pattern
        item["不足理由"] = missing_reason
        item["推奨カフェモデル"] = model
        item["推定席数"] = seats

        for k, v in business.items():
            item[k] = v

        item["初期投資下限"] = initial_low
        item["初期投資上限"] = initial_high
        item["初期投資中央値"] = initial_mid

        score, rank, comment = score_business(item)
        item["事業成立性スコア"] = score
        item["評価点"] = score
        item["評価ランク"] = rank
        item["評価コメント"] = comment
        item["ダッシュボード表示コメント"] = make_dashboard_comment(item)

        rows.append(item)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    dashboard_cols = [
        "物件名", "所在地", "掲載サイト", "詳細URL", "latitude", "longitude",
        "家賃", "家賃_円", "面積", "面積_㎡_補正", "坪数", "坪数_補正", "坪単価",
        "飲食可否", "立地区分", "店舗規模", "物件タイプ推定", "階数判定", "駐車場判定",
        "事業成立パターン", "不足理由", "推奨カフェモデル", "推定席数", "想定客単価",
        "月間固定費", "必要月商", "必要日商_26日営業", "必要日客数_26日営業",
        "初期投資中央値", "事業成立性スコア", "評価ランク", "評価コメント", "ダッシュボード表示コメント"
    ]
    out_df[dashboard_cols].to_csv(DASHBOARD_CSV, index=False, encoding="utf-8-sig")

    display_cols = [
        "評価ランク", "事業成立性スコア", "事業成立パターン", "不足理由", "物件名", "所在地",
        "家賃", "家賃_円", "坪数_補正", "坪単価", "飲食可否", "立地区分", "店舗規模",
        "階数判定", "駐車場判定", "推奨カフェモデル", "推定席数", "月間固定費",
        "必要月商", "必要日客数_26日営業", "初期投資中央値", "掲載サイト", "詳細URL", "評価コメント"
    ]

    html_table = out_df[display_cols].to_html(index=False, escape=False, table_id="cafe_properties", classes="display nowrap")
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>カフェ開業向け物件評価一覧</title>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
<style>
body {{ font-family: sans-serif; margin: 20px; }}
table {{ width: 100%; }}
a {{ color: #0066cc; }}
.note {{ background: #f7f7f7; padding: 12px; border-left: 4px solid #999; margin-bottom: 20px; }}
</style>
</head>
<body>
<h1>カフェ開業向け物件評価一覧</h1>
<div class="note">
<p>この一覧は、統合済み物件CSVをもとにした事業成立性評価です。</p>
<p>A/B/C/Dは立地の良さではなく、必要月商・必要日客数・初期投資・物件条件から見た事業成立性を評価しています。</p>
</div>
{html_table}
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready(function() {{
  $('#cafe_properties').DataTable({{
    pageLength: 25,
    order: [[1, 'desc']],
    columnDefs: [{{
      targets: 21,
      render: function(data, type, row) {{
        if (!data) return "";
        return '<a href="' + data + '" target="_blank">詳細</a>';
      }}
    }}],
    initComplete: function () {{
      this.api().columns([0, 2, 9, 10, 11, 12, 13, 14, 20]).every(function () {{
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
    print(f"[SAVE] {DASHBOARD_CSV}: {len(out_df)}件")
    print(f"[SAVE] {OUTPUT_HTML}")
    print("[RANK]")
    print(out_df["評価ランク"].value_counts().sort_index())
    print("[PATTERN]")
    print(out_df["事業成立パターン"].value_counts())
    print("\n=== 要確認物件 ===")

if __name__ == "__main__":
    main()

