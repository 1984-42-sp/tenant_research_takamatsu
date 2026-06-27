# Procurement Suite README

## 概要

`tenant_research_takamatsu/procurement` は、カフェ開業に必要な仕入先候補、参考価格、原価シミュレーションを管理するサブプロジェクトです。

物件・競合調査とは独立して開発し、最終成果物のみ `tenant_research_takamatsu/docs` に統合します。

## 目的

以下の情報をCSVとHTMLダッシュボードとして整理します。

```text
青果・フルーツ
コーヒー
消耗品・包材
原材料
氷・製氷機
参考価格
メニュー原価
```

## 実行方法

プロジェクトルート `tenant_research_takamatsu` から実行します。

```powershell
python main2.py
```

`main2.py` は `procurement/` 配下のスクリプトを順に呼び出します。

## main2.py の実行フロー

```text
1. procurement/scripts/validate_csvs.py
2. procurement/scripts/generate_masters.py
3. procurement/scripts/prepare_supplier_locations.py
4. procurement/scripts/prepare_map_targets.py
5. procurement/scripts/patch_supplier_coordinates.py
6. procurement/scripts/generate_dashboard.py
7. procurement/scripts/generate_cost_simulator_dashboard.py
8. procurement/scripts/generate_supplier_map.py
9. procurement/scripts/update_docs.py
```

存在しないスクリプトは `[SKIP]` として飛ばします。

## 主要入力CSV

```text
procurement/data/fruit/fruit_suppliers.csv
procurement/data/coffee/coffee_suppliers.csv
procurement/data/consumables/consumables_suppliers.csv
procurement/data/materials/materials_suppliers.csv
procurement/data/ice/ice_suppliers.csv
procurement/data/prices/price_observations.csv
procurement/data/prices/fruit_price_observations.csv
```

原価シミュレーター用：

```text
procurement/data/recipes/menu_master.csv
procurement/data/recipes/recipe_master.csv
procurement/data/recipes/ingredient_master.csv
```

## master CSV

```text
procurement/output/master/supplier_master.csv
procurement/output/master/price_master.csv
procurement/output/master/fruit_price_master.csv
```

`supplier_master.csv` は仕入先DBと原価シミュレーターで共通利用するマスターです。

既存列の削除・名称変更は禁止し、拡張は列追加で行います。

## 主要成果物

```text
procurement/output/dashboard/procurement_dashboard.html
procurement/output/dashboard/procurement_supplier_map.html
procurement/output/dashboard/cost_simulator_dashboard.html
```

`procurement/scripts/update_docs.py` 実行後：

```text
procurement/docs/procurement_dashboard.html
procurement/docs/procurement_supplier_map.html
procurement/docs/cost_simulator_dashboard.html
```

最終的には `tenant_research_takamatsu/scripts/update_docs.py` により、以下へ集約されます。

```text
tenant_research_takamatsu/docs/procurement_dashboard.html
tenant_research_takamatsu/docs/cost_simulator_dashboard.html
```

## ダッシュボードの役割

### procurement_dashboard.html

仕入先候補DBです。

主な機能：

```text
仕入先検索
カテゴリ絞り込み
仕入先詳細
参考価格表示
関連価格表示
比較
```

### procurement_supplier_map.html

ローカル仕入先の地図確認用ダッシュボードです。

### cost_simulator_dashboard.html

メニュー別の原価・原価率・粗利を確認するためのダッシュボードです。

## データ方針

- 公式情報を優先する。
- 推測で項目を埋めない。
- 未確認情報は空欄または `---` 表示にする。
- `order_methods` は注文方法、`wholesale_available` は卸売対応として分離する。
- `delivery_available` は配送可否、`delivery_area` は配送範囲として分離する。
- `supplier_master.csv` は共通マスターとして育てる。

## 公開統合方針

`procurement` 内で成果物を生成した後、ルート側で以下を実行します。

```powershell
python scripts\update_docs.py
```

これにより `procurement/docs` の成果物が `tenant_research_takamatsu/docs` へコピーされます。

## 注意事項

- `procurement` はサブモジュールではなく通常ディレクトリとして管理する。
- `procurement/.git` は置かない。
- `main2.py` は `tenant_research_takamatsu/docs` へ直接コピーしない。
- 公開反映は必ずルート側 `scripts/update_docs.py` で行う。
