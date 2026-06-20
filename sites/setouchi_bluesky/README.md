# 瀬戸内ブルースカイ

## サイト情報

- サイト名: 瀬戸内ブルースカイ
- トップURL: https://www.setouchibluesky.jp
- 一覧URL: https://www.setouchibluesky.jp/kasi-tenpo/kagawa/result/takamatsu-city.html
- 対象エリア: 高松市
- 対象種別: 貸店舗・テナント

## 取得結果

- 一覧取得件数: 5
- 詳細取得件数: 5
- 統合CSV件数: 5
- ジオコーディング成功件数: 5
- ジオコーディング失敗件数: 0

## 飲食店可否

- 可: 1
- 不可: 0
- 不明: 4

## 成果物

### output/setouchi_bluesky/

- setouchi_bluesky_list.csv
- setouchi_bluesky_detail.csv
- setouchi_bluesky.csv
- setouchi_bluesky_geocoded.csv
- setouchi_bluesky_geocode_failed.csv

### output/

- setouchi_bluesky_map.html

## 実行順序

```powershell
python sites\setouchi_bluesky\fetch_list.py
python sites\setouchi_bluesky\inspect_list.py
python sites\setouchi_bluesky\extract.py
python sites\setouchi_bluesky\fetch_detail.py
python sites\setouchi_bluesky\inspect_detail.py
python sites\setouchi_bluesky\extract_detail.py
python sites\setouchi_bluesky\merge.py
python sites\setouchi_bluesky\map.py
python sites\setouchi_bluesky\generate_readme.py
```

## 備考

- 一覧ページは1ページ構成。
- 一覧表示件数は5件。
- 詳細HTMLは5件取得済み。
- 詳細情報は table / th / td 構造から抽出。
- 飲食店可否は「特記事項」「title」「設備」「備考」から判定。
