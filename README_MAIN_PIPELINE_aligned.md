# 高松市 カフェ開業候補地分析システム README_MAIN_PIPELINE

## 目的

本プロジェクトは、高松市内の店舗・事業用賃貸物件、近隣カフェ競合、仕入先候補、原価シミュレーションを統合し、カフェ開業候補地の判断材料を HTML / CSV として出力するための統合プロジェクトです。

単なる物件一覧ではなく、以下を同じ公開成果物群として扱います。

```text
物件データ
競合店舗データ
事業成立性評価
営業シミュレーション
仕入先候補DB
原価シミュレーション
```

## 実行ファイルの役割

### main.py

物件・競合調査の統合パイプラインです。

主な役割：

```text
1. 必要に応じて競合サイト調査を実行
2. 物件CSVを統合
3. カフェ事業性評価を実行
4. 営業シミュレーションを生成
5. 物件・競合統合マップを生成
6. 分析レポートを生成
```

重要：

```text
main.py は scripts/update_docs.py を実行しません。
```

### main2.py

Procurement Suite の統合パイプラインです。

主な役割：

```text
1. 仕入先CSV検証
2. supplier_master / price_master 生成
3. 地図用CSV生成
4. 座標補正
5. procurement_dashboard.html 生成
6. cost_simulator_dashboard.html 生成
7. procurement_supplier_map.html 生成
8. procurement/docs 反映
```

重要：

```text
main2.py は tenant_research_takamatsu/docs には直接反映しません。
```

### scripts/update_docs.py

GitHub Pages 公開用の最終集約スクリプトです。

主な役割：

```text
1. templates/netlify_index.html から docs/index.html を生成
2. output/final_html の物件系HTMLを docs へコピー
3. output/competitors の統合マップを docs/all_properties_map.html としてコピー
4. output/reports の分析レポートを docs へコピー
5. procurement/docs の仕入先・原価系HTMLを docs へコピー
```

## 推奨実行順

通常更新では、プロジェクトルートで以下を順に実行します。

```powershell
python main.py
python main2.py
python scripts\update_docs.py
```

その後、GitHub Pages へ反映します。

```powershell
git add .
git commit -m "Update"
git push origin main
```

## フェーズ構成

### 1. サイト調査フェーズ

必要な場合のみ `main.py` の対話式メニューから実行します。

対象：

```text
食べログ
ホットペッパーグルメ
Googleマップ
```

Googleマップは以下の2モードを選択できます。

```text
B. 一覧取得のみ
A. 一覧取得 + 手動詳細URL取得あり
```

### 2. 物件統合・評価フェーズ

`main.py` が実行します。

主な成果物：

```text
output/final_html/cafe_business_dashboard.html
output/final_html/business_plan_dashboard.html
output/final_html/simulation_index.html
output/final_html/property_business_simulations/
output/competitors/integrated_property_map.html
output/reports/cafe_business_analysis_report.html
```

### 3. Procurement Suite フェーズ

`main2.py` が実行します。

主な成果物：

```text
procurement/output/dashboard/procurement_dashboard.html
procurement/output/dashboard/cost_simulator_dashboard.html
procurement/output/dashboard/procurement_supplier_map.html
procurement/docs/procurement_dashboard.html
procurement/docs/cost_simulator_dashboard.html
procurement/docs/procurement_supplier_map.html
```

### 4. 公開反映フェーズ

`scripts/update_docs.py` が実行します。

主な成果物：

```text
docs/index.html
docs/all_properties_map.html
docs/cafe_business_dashboard.html
docs/business_plan_dashboard.html
docs/simulation_index.html
docs/cafe_business_analysis_report.html
docs/procurement_dashboard.html
docs/cost_simulator_dashboard.html
```

## ディレクトリ概要

```text
tenant_research_takamatsu/
├─ main.py
├─ main2.py
├─ scripts/
├─ sites/
├─ procurement/
├─ output/
├─ templates/
└─ docs/
```

## 注意事項

- `main.py` と `main2.py` は公開反映を行わない。
- `scripts/update_docs.py` は最終公開用の集約だけを担当する。
- `docs/` は GitHub Pages 公開対象のため、手作業で編集せずスクリプト生成を基本とする。
- 物件評価・競合統合・仕入先DB・原価シミュレーションは分離して管理し、公開時だけ `docs/` に集約する。
- 推測でデータを埋めない。未確認情報は空欄または `---` 表示とする。
