# テナントショップ

## サイト情報

- サイト名: テナントショップ
- ベースURL: https://www.tenant-shop.jp
- 詳細URL: https://www.tenant-shop.jp/detail/e-527623/

## 取得結果

- 詳細CSV: 1件 / 27列
- 統合CSV: 1件 / 27列
- ジオコード済みCSV: 1件 / 31列
- ジオコード失敗CSV: 0件 / 0列
- 地図HTML: 生成済み

## 件数

- 詳細取得: 1件
- ジオコード成功: 1件
- ジオコード失敗: 0件

## 実行順序

```powershell
python sites\tenant_shop\fetch_detail.py
python sites\tenant_shop\inspect_detail.py
python sites\tenant_shop\extract_detail.py
python sites\tenant_shop\merge.py
python sites\tenant_shop\map.py
python sites\tenant_shop\generate_readme.py
```

## 成果物

```text
output/tenant_shop/tenant_shop_detail.csv
output/tenant_shop/tenant_shop.csv
output/tenant_shop/tenant_shop_geocoded.csv
output/tenant_shop/tenant_shop_geocode_failed.csv
output/tenant_shop_map.html
sites/tenant_shop/selectors.py
sites/tenant_shop/README.md
```

## 備考

- テナントショップで発見した高松市の物件1件を個別取得。
- 一覧取得は行わず、詳細URLから直接取得。
- ジオコード成功。
