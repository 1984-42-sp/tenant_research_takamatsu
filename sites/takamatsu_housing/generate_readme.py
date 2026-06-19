from pathlib import Path
from datetime import date

import pandas as pd

OUTPUT_DIR = Path("output/takamatsu_housing")
README_PATH = Path("sites/takamatsu_housing/README.md")

CSV_PATH = OUTPUT_DIR / "takamatsu_housing.csv"
GEOCODED_PATH = OUTPUT_DIR / "takamatsu_housing_geocoded.csv"
FAILED_PATH = OUTPUT_DIR / "takamatsu_housing_geocode_failed.csv"
LIST_PATH = OUTPUT_DIR / "takamatsu_housing_list.csv"
DETAIL_PATH = OUTPUT_DIR / "takamatsu_housing_detail.csv"
MAP_PATH = OUTPUT_DIR / "takamatsu_housing_map.html"

df = pd.read_csv(CSV_PATH)
df_geo = pd.read_csv(GEOCODED_PATH)
df_failed = pd.read_csv(FAILED_PATH)
df_list = pd.read_csv(LIST_PATH)
df_detail = pd.read_csv(DETAIL_PATH)

total_count = len(df)
column_count = len(df.columns)
list_count = len(df_list)
detail_count = len(df_detail)

duplicate_count = df["article_id"].duplicated().sum()
geo_success = df_geo["latitude"].notna().sum()
geo_failed = len(df_failed)

restaurant_counts = df["飲食店可否"].value_counts(dropna=False).to_dict()

restaurant_ok = restaurant_counts.get("可", 0)
restaurant_ng = restaurant_counts.get("不可", 0)
restaurant_unknown = restaurant_counts.get("不明", 0)

today = date.today()

readme = f"""# 高松ハウジングサービス 攻略記録

## 概要

対象サイト: 高松ハウジングサービス

サイトURL: https://www.takamatsuhousing.jp

対象ページ: https://www.takamatsuhousing.jp/kasi-tenpo/kagawa/result/takamatsu-city.html

対象地域: 香川県高松市

対象種別: 貸店舗・テナント

取得日: {today}

---

## 取得結果

|項目|件数|
|---|---:|
|一覧取得件数|{list_count}|
|詳細取得件数|{detail_count}|
|統合件数|{total_count}|
|統合列数|{column_count}|
|重複件数|{duplicate_count}|
|ジオコーディング成功|{geo_success}|
|ジオコーディング失敗|{geo_failed}|

---

## 飲食店可否

|区分|件数|
|---|---:|
|可|{restaurant_ok}|
|不可|{restaurant_ng}|
|不明|{restaurant_unknown}|

---

## 成果物

|ファイル|内容|
|---|---|
|output/takamatsu_housing_list.csv|一覧ページ由来データ|
|output/takamatsu_housing_detail.csv|詳細ページ由来データ|
|output/takamatsu_housing.csv|統合CSV|
|output/takamatsu_housing_geocoded.csv|緯度経度付きCSV|
|output/takamatsu_housing_geocode_failed.csv|ジオコーディング失敗物件一覧|
|output/takamatsu_housing_map.html|地図HTML|

---

## 再取得手順

1. 一覧HTML取得

    python sites\\takamatsu_housing\\fetch_list.py

2. 一覧HTML構造確認

    python sites\\takamatsu_housing\\inspect_list.py

3. 一覧データ抽出

    python sites\\takamatsu_housing\\extract.py

4. 詳細HTML取得

    python sites\\takamatsu_housing\\fetch_detail.py

5. 詳細HTML構造確認

    python sites\\takamatsu_housing\\inspect_detail.py

6. 詳細データ抽出

    python sites\\takamatsu_housing\\extract_detail.py

7. データ統合

    python sites\\takamatsu_housing\\merge.py

8. 地図生成

    python sites\\takamatsu_housing\\map.py

9. README更新

    python sites\\takamatsu_housing\\generate_readme.py

---

## 備考

一覧ページは4ページ構成。

1ページ目から3ページ目は各30件。

4ページ目は27件。

合計117件。

ジオコーディングは全117件成功。

飲食店可否は詳細ページの「特記事項」欄をもとに判定。

「飲食店不可」が含まれる場合は不可。

「飲食店可」「軽飲食」「重飲食」が含まれる場合は可。

該当文言がない場合は不明。
"""

README_PATH.write_text(
    readme,
    encoding="utf-8"
)

print(f"saved: {README_PATH}")
print("list:", list_count)
print("detail:", detail_count)
print("merged:", total_count)
print("columns:", column_count)
print("duplicated:", duplicate_count)
print("geocode success:", geo_success)
print("geocode failed:", geo_failed)
print("restaurant ok:", restaurant_ok)
print("restaurant ng:", restaurant_ng)
print("restaurant unknown:", restaurant_unknown)