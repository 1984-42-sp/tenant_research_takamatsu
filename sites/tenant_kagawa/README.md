# テナント香川 攻略記録

## 概要

対象サイト: tenantkagawa.com

対象地域: 香川県高松市

取得日: 2026-06-19

---

## 取得結果

|項目|件数|
|---|---:|
|統合件数|49|
|統合列数|55|
|重複件数|0|
|ジオコーディング成功|31|
|ジオコーディング失敗|18|

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

# 再取得手順

## 1. 検索実行

```powershell
python sites\tenant_kagawa\fetch_top.py
```

目的:

- 高松市を選択
- 検索実行
- 検索結果ページへ遷移

---

## 2. 一覧HTML取得

```powershell
python sites\tenant_kagawa\fetch_list.py
```

生成物:

```text
data/html/tenant_kagawa/

list_page_1.html
list_page_2.html
list_page_3.html
list_page_4.html
list_page_5.html
```

確認事項:

- 取得件数が49件であること
- ページ数が5ページであること

---

## 3. 詳細HTML取得

```powershell
python sites\tenant_kagawa\fetch_detail.py
```

生成物:

```text
data/html/tenant_kagawa/detail/
```

確認事項:

- 詳細HTMLが49件取得されていること

---

## 4. 一覧データ解析

```powershell
python sites\tenant_kagawa\extract.py
```

生成物:

```text
output/tenant_kagawa_list.csv
```

確認事項:

- レコード数49件

---

## 5. 詳細データ解析

```powershell
python sites\tenant_kagawa\extract_detail.py
```

生成物:

```text
output/tenant_kagawa_detail.csv
```

確認事項:

- レコード数49件

---

## 6. データ統合

```powershell
python sites\tenant_kagawa\merge.py
```

生成物:

```text
output/tenant_kagawa.csv
```

確認事項:

- 件数49件
- 重複件数0件

---

## 7. ジオコーディング・地図生成

```powershell
python sites\tenant_kagawa\map.py
```

生成物:

```text
output/tenant_kagawa_geocoded.csv
output/tenant_kagawa_geocode_failed.csv
output/tenant_kagawa_map.html
```

確認事項:

- ジオコーディング成功件数確認
- ジオコーディング失敗件数確認
- 地図HTML生成確認

---

## 8. README更新

```powershell
python sites\tenant_kagawa\generate_readme.py
```

生成物:

```text
sites/tenant_kagawa/README.md
```

確認事項:

- 件数情報が最新化されていること

---

## 完了後

```powershell
git add .
git commit -m "Update tenant_kagawa data"
```

成果物:

- HTML取得完了
- CSV生成完了
- 地図生成完了
- README更新完了