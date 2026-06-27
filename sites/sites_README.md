# sites README

## 概要

`tenant_research_takamatsu/sites` は、物件サイトおよび Googleマップ競合店舗情報を取得・抽出するためのサイト別スクリプト置き場です。

このディレクトリは、主に「取得フェーズ」を担当します。取得済みCSVの統合・評価・公開HTML生成は、ルートの `main.py` および `scripts/` 側が担当します。

## 現在のディレクトリ構成

```text
sites/
├─ google_maps/
├─ mcrea/
├─ scripts/
├─ setouchi_bluesky/
├─ takamatsu_housing/
├─ tenant_kagawa/
├─ tenant_shop/
├─ uemura_re/
└─ _template/
```

## 各ディレクトリの役割

### google_maps

Googleマップ上のカフェ競合店舗を取得・抽出するためのスクリプト群です。

主な実行パターン：

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

Googleマップ取得はブラウザ上の手動操作を含みます。

### tenant_kagawa

テナント香川の物件取得・抽出用ディレクトリです。

代表的な流れ：

```text
検索ページ取得
一覧HTML取得
詳細HTML取得
一覧CSV抽出
詳細CSV抽出
統合CSV生成
```

### takamatsu_housing

高松ハウジングサービスの物件取得・抽出用ディレクトリです。

### mcrea

エムクレアの物件取得・抽出用ディレクトリです。

### setouchi_bluesky

瀬戸内ブルースカイの物件取得・抽出用ディレクトリです。

### tenant_shop

テナントショップの物件取得・抽出用ディレクトリです。

### uemura_re

植村不動産の物件取得・抽出用ディレクトリです。

### _template

新しい物件サイトを追加するときのテンプレートです。

サイト追加時はこの構成を参考にします。

### scripts

`sites` 配下で共通利用する補助スクリプトを置くためのディレクトリです。

## sites の責務

`sites` は以下を担当します。

```text
Webページ取得
HTML保存
サイト別CSV抽出
必要に応じた詳細CSV生成
```

以下は担当しません。

```text
全サイトCSV統合
カフェ事業性評価
競合統合
公開HTML生成
docs 反映
```

これらはルートの `main.py` と `scripts/` 側で行います。

## サイト追加時の基本方針

新しいサイトを追加する場合は、以下の流れを基本とします。

```text
1. sites/_template を参考にサイト用ディレクトリを作成
2. fetch 系スクリプトでHTMLを保存
3. extract 系スクリプトでCSV化
4. merge 系スクリプトでサイト単位CSVを生成
5. scripts/merge_all_properties.py の統合対象に追加
```

## 注意事項

- 取得・抽出・統合の役割を混ぜない。
- サイト別ディレクトリ内では、対象サイト固有の処理に限定する。
- 統合後の評価ロジックは `scripts/` 側で管理する。
- 手動操作が必要なサイトは、READMEやスクリプト内コメントに操作手順を残す。
- 推測で物件条件を埋めない。
- 取得できない項目は空欄で維持する。
