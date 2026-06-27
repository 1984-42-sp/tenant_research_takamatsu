# scripts README

## 概要

`tenant_research_takamatsu/scripts` は、物件CSV統合、カフェ事業性評価、競合統合、レポート生成、GitHub Pages 公開用 `docs/` 反映を担当するスクリプト群です。

現在の通常運用では、個別スクリプトを直接順番に実行するのではなく、基本的に以下のどちらかから呼び出します。

```powershell
python main.py
python scripts\update_docs.py
```

## main.py から実行される主な処理

### サイト調査フェーズ

必要な場合のみ対話式に実行します。

```text
scripts/competitors/run_tabelog_competitors_pipeline.py
scripts/competitors/fetch_hotpepper_competitors.py
sites/google_maps/fetch_search.py
sites/google_maps/extract.py
sites/google_maps/extract_details.py
sites/google_maps/attach_coords.py
scripts/competitors/normalize_competitors.py
```

### 物件統合・評価フェーズ

```text
scripts/merge_all_properties.py
scripts/evaluate_cafe_properties_v2.py
scripts/generate_business_plan_dashboard_csv.py
scripts/generate_business_plan_dashboard_html.py
scripts/generate_property_business_simulations.py
scripts/generate_cafe_business_dashboard.py
scripts/generate_enhanced_property_map.py
```

主な出力先：

```text
output/all_properties/
output/final_html/
output/archive_csv/
```

### 競合統合・最終出力フェーズ

```text
scripts/competitors/merge_property_competitors.py
scripts/competitors/merge_dashboard_competitors.py
scripts/competitors/generate_integrated_enhanced_property_map.py
scripts/reports/generate_cafe_business_analysis_report.py
```

主な出力先：

```text
output/competitors/
output/reports/
```

## scripts/update_docs.py の役割

`scripts/update_docs.py` は公開用 `docs/` を再生成する最終工程です。

実行：

```powershell
python scripts\update_docs.py
```

処理内容：

```text
1. docs/ を一度クリア
2. templates/netlify_index.html から docs/index.html を生成
3. output/competitors/integrated_property_map.html を docs/all_properties_map.html としてコピー
4. output/final_html/ の主要HTMLを docs/ にコピー
5. output/reports/ の分析レポートを docs/ にコピー
6. procurement/docs/ の仕入先・原価系HTMLを docs/ にコピー
7. property_business_simulations/ ディレクトリを docs/ にコピー
```

公開対象：

```text
docs/index.html
docs/all_properties_map.html
docs/business_plan_dashboard.html
docs/cafe_business_dashboard.html
docs/simulation_index.html
docs/cafe_business_analysis_report.html
docs/procurement_dashboard.html
docs/cost_simulator_dashboard.html
docs/property_business_simulations/
```

## 実行上の注意

- `main.py` は `scripts/update_docs.py` を呼び出しません。
- `main2.py` も `tenant_research_takamatsu/docs` へは直接反映しません。
- GitHub Pages 公開物は必ず最後に `python scripts\update_docs.py` で集約します。
- `docs/` は毎回クリアされるため、手作業で置いたファイルは消える可能性があります。
- `HOTPEPPER_API_KEY` が必要な処理は、環境変数を事前設定するか、`main.py` の対話入力で対応します。

## 手動実行が必要になりやすい処理

Googleマップ調査はブラウザ操作を含むため、完全自動ではありません。

一覧取得のみ：

```powershell
python sites\google_maps\fetch_search.py
python sites\google_maps\extract.py
python sites\google_maps\attach_coords.py
python scripts\competitors\normalize_competitors.py
```

一覧取得 + 手動詳細URL取得あり：

```powershell
python sites\google_maps\fetch_search.py
python sites\google_maps\extract_details.py
Copy-Item output\google_maps\google_maps_cafes_from_details.csv output\google_maps\google_maps_geocoded.csv -Force
python scripts\competitors\normalize_competitors.py
```

## 注意事項

- 物件評価は `all_properties.csv` を基準に行う。
- 高評価物件だけでなく、全物件を閲覧可能な構成を維持する。
- 推測で物件条件や競合情報を補完しない。
- 公開HTMLの最終配置は `scripts/update_docs.py` に集約する。
