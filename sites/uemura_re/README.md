# 植村不動産

## サイト情報

- サイト名: 植村不動産
- ベースURL: https://www.uemura-re.jp
- 一覧URL: https://www.uemura-re.jp/kasi-tenpo/kagawa/result/takamatsu-city.html
- 追加詳細URL: https://www.uemura-re.jp/kasi-other/detail-682728ded63cad74d6bc85b5/

## 取得結果

- 一覧CSV: 4件 / 5列
- 詳細CSV: 5件 / 52列
- 統合CSV: 5件 / 54列
- ジオコード済みCSV: 5件 / 56列
- ジオコード失敗CSV: 1件 / 54列
- 地図HTML: 生成済み

## 件数

- 貸店舗一覧: 4件
- 貸ビル・貸倉庫・その他: 1件
- 合計: 5件

## 実行順序

```powershell
python sites\uemura_re\fetch_list.py
python sites\uemura_re\inspect_list.py
python sites\uemura_re\extract.py
python sites\uemura_re\fetch_detail.py
python sites\uemura_re\inspect_detail.py
python sites\uemura_re\extract_detail.py
python sites\uemura_re\merge.py
python sites\uemura_re\map.py
python sites\uemura_re\generate_readme.py
```

## 成果物

```text
output/uemura_re/uemura_re_list.csv
output/uemura_re/uemura_re_detail.csv
output/uemura_re/uemura_re.csv
output/uemura_re/uemura_re_geocoded.csv
output/uemura_re/uemura_re_geocode_failed.csv
output/uemura_re_map.html
sites/uemura_re/selectors.py
sites/uemura_re/README.md
```

## 備考

- 一覧ページは1ページ。
- 貸店舗4件を一覧から取得。
- 貸ビル・貸倉庫・その他1件は詳細URLを直接追加。
- 詳細ページは5件取得。
- ジオコード成功4件、失敗1件。
