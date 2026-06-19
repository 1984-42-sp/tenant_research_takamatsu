from pathlib import Path
from datetime import date

import pandas as pd

OUTPUT_DIR = Path("output")
README_PATH = Path(
    "sites/tenant_kagawa/README.md"
)

df = pd.read_csv(
    OUTPUT_DIR / "tenant_kagawa.csv"
)

df_geo = pd.read_csv(
    OUTPUT_DIR / "tenant_kagawa_geocoded.csv"
)

df_failed = pd.read_csv(
    OUTPUT_DIR / "tenant_kagawa_geocode_failed.csv"
)

total_count = len(df)

column_count = len(df.columns)

duplicate_count = (
    df["article_id"]
    .duplicated()
    .sum()
)

geo_success = (
    df_geo["latitude"]
    .notna()
    .sum()
)

geo_failed = len(df_failed)

today = date.today()

readme = f"""# テナント香川 攻略記録

## 概要

対象サイト: tenantkagawa.com

対象地域: 香川県高松市

取得日: {today}

---

## 取得結果

|項目|件数|
|---|---:|
|統合件数|{total_count}|
|統合列数|{column_count}|
|重複件数|{duplicate_count}|
|ジオコーディング成功|{geo_success}|
|ジオコーディング失敗|{geo_failed}|

---

## 成果物

- output/tenant_kagawa_list.csv
- output/tenant_kagawa_detail.csv
- output/tenant_kagawa.csv
- output/tenant_kagawa_geocoded.csv
- output/tenant_kagawa_geocode_failed.csv
- output/tenant_kagawa_map.html

---

## 備考

一覧ページ取得完了

詳細ページ取得完了

CSV統合完了

地図生成完了

ジオコーディング失敗物件は
tenant_kagawa_geocode_failed.csv
に保存
"""

README_PATH.write_text(
    readme,
    encoding="utf-8"
)

print(
    f"saved: {README_PATH}"
)