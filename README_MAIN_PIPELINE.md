# 高松市 カフェ開業候補地データベース構築プロジェクト

## メイン実行パイプライン

このプロジェクトでは、各サイトのスクレイピング完了後の統合分析処理を

```powershell
python main.py
```

で一括実行する。

---

## 対象業態

韓国ソンス風フルーツ主体カフェ

商品構成：

* パフェ
* フルーツドリンク
* コーヒー
* 夏季かき氷

前提：

* 焼菓子主体ではない
* ランチ主体ではない
* ワンオペ不採用
* 常時2名以上
* カウンターオペレーション型

---

## 実行フロー

main.py は以下を順番に実行する。

### 1

```text
scripts/merge_all_properties.py
```

サイト別CSVを統合し、

```text
output/all_properties/
```

へ出力する。

生成物：

```text
all_properties.csv
all_properties_geocoded.csv
all_properties_geocode_failed.csv
all_properties_map.html
all_properties_list.html
```

---

### 2

```text
scripts/evaluate_cafe_properties_v2.py
```

カフェ事業成立性評価を実施。

生成物：

```text
cafe_property_evaluation.csv
cafe_property_evaluation.html
```

---

### 3

```text
scripts/generate_property_business_simulations.py
```

物件別営業シミュレーション生成。

生成物：

```text
property_business_simulations/
property_business_simulations_index.csv
index.html
```

---

### 4

```text
scripts/generate_cafe_business_dashboard.py
```

事業成立性ダッシュボード生成。

生成物：

```text
cafe_business_dashboard.csv
cafe_business_dashboard.html
```

---

### 5

```text
scripts/generate_business_plan_dashboard_csv.py
```

Phase5ランキング用CSV生成。

生成物：

```text
business_plan_dashboard.csv
```

---

### 6

```text
scripts/generate_business_plan_dashboard_html.py
```

Phase5ランキングHTML生成。

生成物：

```text
business_plan_dashboard.html
```

---

### 7

main.py による成果物整理

生成後、

```text
output/final_html/
```

へ最終成果物を移動。

---

## 最終成果物

### 基礎DB

```text
all_properties_map.html
all_properties_list.html
```

---

### 事業性評価

```text
cafe_property_evaluation.html
```

---

### 意思決定支援

```text
cafe_business_dashboard.html
business_plan_dashboard.html
```

---

### 営業シミュレーション

```text
simulation_index.html

property_business_simulations/
```

---

## CSV保管先

分析用CSVは

```text
output/archive_csv/
```

へ移動される。

---

## 注意事項

* all_properties.csv を正本とする
* 重複削除は本格適用しない
* 推測禁止
* 実データ優先
* 事業成立性評価を最優先とする
* 高評価物件だけでなく全物件を閲覧可能とする
