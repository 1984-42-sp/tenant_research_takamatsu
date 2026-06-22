# エムクレア

## サイト情報

- サイト名: エムクレア
- ベースURL: https://www.mcrea.jp
- 一覧URL1: https://www.mcrea.jp/kasi-tenpo/kagawa/result/takamatsu-city.html
- 一覧URL2: https://www.mcrea.jp/kasi-tenpo/kagawa/result/takamatsu-city.html?page=2

## 取得結果

- 一覧CSV: 42件 / 6列
- 詳細CSV: 42件 / 53列
- 統合CSV: 42件 / 58列
- ジオコード済みCSV: 42件 / 60列
- ジオコード失敗CSV: 1件 / 58列
- 地図HTML: 生成済み

## 件数

- 一覧取得: 42件
- 詳細取得: 42件
- ジオコード成功: 41件
- ジオコード失敗: 1件

## 実行順序

```powershell
python sites\mcrea\fetch_list_manual.py
python sites\mcrea\inspect_list.py
python sites\mcrea\extract.py
python sites\mcrea\fetch_detail.py
python sites\mcrea\inspect_detail.py
python sites\mcrea\extract_detail.py
python sites\mcrea\merge.py
python sites\mcrea\map.py
python sites\mcrea\generate_readme.py
```

## 成果物

```text
output/mcrea/mcrea_list.csv
output/mcrea/mcrea_detail.csv
output/mcrea/mcrea.csv
output/mcrea/mcrea_geocoded.csv
output/mcrea/mcrea_geocode_failed.csv
output/mcrea_map.html
sites/mcrea/selectors.py
sites/mcrea/README.md
```

## 備考

- 一覧は2ページ。
- 高松市＋飲食店可の条件で42件を取得。
- 通常のrequests直取得では飲食店可条件が外れるため、fetch_list_manual.pyで手動検索後にHTML保存した。
- mcrea.jpは接続が不安定で、Playwright timeout / ReadTimeout / SSL handshake timeout が発生した。
- 詳細HTML取得では retry / skip / sleep / Connection: close を使用した。
- 今後のテンプレートには fetch_with_retry、既取得ファイルskip、sleep制御を標準搭載することを推奨。
