# 高松ハウジングサービス 攻略記録

## 概要

対象サイト: 高松ハウジングサービス

サイトURL: https://www.takamatsuhousing.jp

対象ページ: https://www.takamatsuhousing.jp/kasi-tenpo/kagawa/result/takamatsu-city.html

対象地域: 香川県高松市

対象種別: 貸店舗・テナント

取得日: 2026-06-23

---

## 取得結果

|項目|件数|
|---|---:|
|一覧取得件数|117|
|詳細取得件数|117|
|統合件数|117|
|統合列数|37|
|重複件数|0|
|ジオコーディング成功|117|
|ジオコーディング失敗|0|

---

## 飲食店可否

|区分|件数|
|---|---:|
|可|41|
|不可|14|
|不明|62|

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

    python sites\takamatsu_housing\fetch_list.py

2. 一覧HTML構造確認

    python sites\takamatsu_housing\inspect_list.py

3. 一覧データ抽出

    python sites\takamatsu_housing\extract.py

4. 詳細HTML取得

    python sites\takamatsu_housing\fetch_detail.py

5. 詳細HTML構造確認

    python sites\takamatsu_housing\inspect_detail.py

6. 詳細データ抽出

    python sites\takamatsu_housing\extract_detail.py

7. データ統合

    python sites\takamatsu_housing\merge.py

8. 地図生成

    python sites\takamatsu_housing\map.py

9. README更新

    python sites\takamatsu_housing\generate_readme.py

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
