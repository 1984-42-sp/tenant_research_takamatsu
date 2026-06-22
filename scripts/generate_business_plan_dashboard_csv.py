from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"
OUTPUT_CSV = BASE_DIR / "output" / "all_properties" / "business_plan_dashboard.csv"


def to_float(value, default=0.0):
    if pd.isna(value):
        return default
    text = str(value).replace(",", "").replace("円", "").replace("㎡", "").replace("坪", "").strip()
    match = re.search(r"-?\d+(\.\d+)?", text)
    if not match:
        return default
    return float(match.group())


def score_space_openness(row):
    tsubo = to_float(row.get("坪数_補正"))
    seats = to_float(row.get("推定席数"))

    if tsubo <= 0:
        return 20

    seat_density = seats / tsubo if seats > 0 else 0

    # 面積帯評価：ソンス風実装の現実性
    if tsubo < 8:
        base = 10
    elif tsubo < 10:
        base = 20
    elif tsubo < 15:
        base = 38
    elif tsubo < 20:
        base = 58
    elif tsubo < 30:
        base = 78
    elif tsubo < 45:
        base = 90
    elif tsubo < 60:
        base = 95
    elif tsubo < 80:
        base = 88
    else:
        base = 75

    # 席密度評価：詰め込みすぎを減点
    if seat_density == 0:
        density_adj = 0
    elif seat_density <= 0.45:
        density_adj = 8
    elif seat_density <= 0.65:
        density_adj = 4
    elif seat_density <= 0.85:
        density_adj = -3
    else:
        density_adj = -12

    return max(0, min(100, base + density_adj))

def score_space_openness(row):
    tsubo = to_float(row.get("坪数_補正"))
    seats = to_float(row.get("推定席数"))

    if tsubo <= 0:
        return 20

    seat_density = seats / tsubo if seats > 0 else 0

    # 面積帯評価：ソンス風実装の現実性
    if tsubo < 8:
        base = 10
    elif tsubo < 10:
        base = 20
    elif tsubo < 15:
        base = 38
    elif tsubo < 20:
        base = 58
    elif tsubo < 30:
        base = 78
    elif tsubo < 45:
        base = 90
    elif tsubo < 60:
        base = 95
    elif tsubo < 80:
        base = 88
    else:
        base = 75

    # 席密度評価：詰め込みすぎを減点
    if seat_density == 0:
        density_adj = 0
    elif seat_density <= 0.45:
        density_adj = 8
    elif seat_density <= 0.65:
        density_adj = 4
    elif seat_density <= 0.85:
        density_adj = -3
    else:
        density_adj = -12

    return max(0, min(100, base + density_adj))

def score_seongsu_design(row):
    tsubo = to_float(row.get("坪数_補正"))
    property_type = str(row.get(" 物件タイプ推定", ""))
    scale = str(row.get("店舗規模", ""))
    floor = str(row.get("階数判定", ""))

    score = 40

    # 面積によるソンス風実装余地
    if 30 <= tsubo < 60:
        score += 35
    elif 20 <= tsubo < 30:
        score += 25
    elif 15 <= tsubo < 20:
        score += 15
    elif 10 <= tsubo < 15:
        score += 5
    elif tsubo < 10:
        score -= 25
    elif tsubo >= 60:
        score += 20

    # 物件タイプ補正
    if "倉庫" in property_type or "工場" in property_type:
        score += 25
    elif "スケルトン" in property_type:
        score += 18
    elif "店舗" in property_type:
        score += 12
    elif "事務所" in property_type:
        score += 6
    elif "居抜" in property_type:
        score += 4

    # 路面・1階補正
    if "1階" in floor or "1F" in floor or "路面" in property_type:
        score += 12
    elif "上階" in floor or "2階以上" in floor:
        score -= 8

    # 極小区画は最終的に抑制
    if tsubo < 8:
        score = min(score, 35)
    elif tsubo < 10:
        score = min(score, 45)

    return max(0, min(100, score))

def score_night_business(row):
    location = str(row.get("立地区分", ""))
    address = str(row.get("所在地", ""))

    score = 45

    center_keywords = ["瓦町", "丸亀町", "常磐町", "古馬場", "片原町", "兵庫町", "南新町", "鍛冶屋町", "亀井町", "今新町", "百間町"]
    station_keywords = ["高松駅", "瓦町駅", "片原町駅"]

    if any(k in address for k in center_keywords):
        score += 35
    elif any(k in address for k in station_keywords):
        score += 30

    if "中心" in location or "駅前" in location or "商業" in location:
        score += 20
    elif "郊外" in location:
        score += 8
    elif "住宅" in location:
        score += 3

    return max(0, min(100, score))


def score_parking_destination(row):
    parking = str(row.get("駐車場判定", ""))
    location = str(row.get("立地区分", ""))

    score = 30

    if "あり" in parking or "有" in parking:
        score += 45
    elif "不明" in parking or parking.strip() == "":
        score += 20
    elif "なし" in parking or "無" in parking:
        score += 0

    if "郊外" in location:
        score += 15
    elif "中心" in location:
        score += 5

    return max(0, min(100, score))


def score_investment_reality(row):
    rent = to_float(row.get("家賃_円"))
    tsubo = to_float(row.get("坪数_補正"))
    initial_investment = to_float(row.get("初期投資中央値"))

    score = 100

    if rent >= 400000:
        score -= 35
    elif rent >= 300000:
        score -= 25
    elif rent >= 220000:
        score -= 15
    elif rent >= 150000:
        score -= 5

    if tsubo >= 60:
        score -= 25
    elif tsubo >= 45:
        score -= 15
    elif tsubo >= 35:
        score -= 8

    if initial_investment >= 30000000:
        score -= 20
    elif initial_investment >= 22000000:
        score -= 10

    return max(0, min(100, score))


def score_fruit_cafe_business(row):
    score = to_float(row.get("事業成立性スコア"), 50)
    return max(0, min(100, score))


def stars_from_score(score):
    if score >= 76:
        return "★★★★★"
    if score >= 70:
        return "★★★★☆"
    if score >= 60:
        return "★★★☆☆"
    if score >= 45:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def fit_type(row):
    score = row["seongsu_fit_score"]
    tsubo = to_float(row.get("坪数_補正"))
    parking = str(row.get("駐車場判定", ""))
    address = str(row.get("所在地", ""))

    center_keywords = ["瓦町", "丸亀町", "常磐町", "古馬場", "片原町", "兵庫町", "南新町", "鍛冶屋町"]

    if score >= 85 and tsubo >= 30:
        return "理想リノベ型"
    if score >= 75 and any(k in address for k in center_keywords):
        return "中心街夜カフェ型"
    if score >= 70 and ("あり" in parking or "有" in parking):
        return "目的地ドライブ型"
    if score >= 60 and tsubo < 20:
        return "小型ミニマム実装型"
    if score >= 60:
        return "標準テナント実装型"
    return "実装難度高"


def fit_comment(row):
    score = row["seongsu_fit_score"]
    stars = row["seongsu_fit_stars"]
    tsubo = to_float(row.get("坪数_補正"))
    space = row["space_openness_score"]
    night = row["night_business_score"]
    parking = row["parking_destination_score"]
    invest = row["investment_reality_score"]

    if score >= 90:
        lead = "韓国ソンス風フルーツカフェの理想実装候補。"
    elif score >= 80:
        lead = "韓国ソンス風の世界観を高い水準で実装しやすい候補。"
    elif score >= 65:
        lead = "条件を整理すれば韓国ソンス風として成立する候補。"
    elif score >= 50:
        lead = "ブランド実装には制約があり、設計上の工夫が必要。"
    else:
        lead = "韓国ソンス風の実装難度が高い候補。"

    notes = []

    if space >= 80:
        notes.append("空間の余白・開放感を作りやすい")
    elif space < 50:
        notes.append("面積または席密度の面で余白確保に課題がある")

    if night >= 80:
        notes.append("夜カフェ・夜パフェ需要との相性が高い")
    elif night < 50:
        notes.append("夜営業の集客導線は弱め")

    if parking >= 75:
        notes.append("駐車場・目的地来店との相性が良い")
    elif parking < 45:
        notes.append("車来店需要の取り込みには課題がある")

    if invest < 55:
        notes.append("投資負担や家賃負担には注意が必要")

    note_text = "、".join(notes) if notes else "大きな突出条件は少ないが、標準的な検討対象。"

    return f"{lead} 星評価は{stars}。坪数は約{tsubo:.1f}坪で、{note_text}。"


def main():
    df = pd.read_csv(INPUT_CSV)
    # Phase5では、飲食可の物件のみをランキング対象にする
    df["飲食可否"] = df["飲食可否"].fillna("").astype(str)
    df = df[df["飲食可否"].str.contains("可", na=False)].copy()
    df = df.reset_index(drop=True)
    df["space_openness_score"] = df.apply(score_space_openness, axis=1)
    df["seongsu_design_score"] = df.apply(score_seongsu_design, axis=1)
    df["night_business_score"] = df.apply(score_night_business, axis=1)
    df["parking_destination_score"] = df.apply(score_parking_destination, axis=1)
    df["investment_reality_score"] = df.apply(score_investment_reality, axis=1)
    df["fruit_cafe_business_score"] = df.apply(score_fruit_cafe_business, axis=1)

    df["seongsu_fit_score"] = (
        df["space_openness_score"] * 0.28
        + df["seongsu_design_score"] * 0.27
        + df["night_business_score"] * 0.18
        + df["parking_destination_score"] * 0.12
        + df["investment_reality_score"] * 0.08
        + df["fruit_cafe_business_score"] * 0.07
    ).round(1)

    df["seongsu_fit_stars"] = df["seongsu_fit_score"].apply(stars_from_score)

    df = df.sort_values("seongsu_fit_score", ascending=False).reset_index(drop=True)
    df["seongsu_rank"] = df.index + 1

    df["seongsu_fit_type"] = df.apply(fit_type, axis=1)
    df["seongsu_fit_comment"] = df.apply(fit_comment, axis=1)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[LOAD] {INPUT_CSV}")
    print(f"[SAVE] {OUTPUT_CSV}")
    print(f"[ROWS] {len(df)}")

    print("\n[STAR SUMMARY]")
    print(df["seongsu_fit_stars"].value_counts().sort_index())

    print("\n[TOP 10]")
    cols = [
        "seongsu_rank",
        "物件名",
        "所在地",
        "seongsu_fit_score",
        "seongsu_fit_stars",
        "seongsu_fit_type",
        "坪数_補正",
        "家賃",
        "駐車場判定",
        "seongsu_design_score",
        "space_openness_score",
        "night_business_score",
    ]
    print(df[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()

