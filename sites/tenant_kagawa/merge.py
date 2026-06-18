import pandas as pd

df_list = pd.read_csv(
    "output/tenant_kagawa_list.csv"
)

df_detail = pd.read_csv(
    "output/tenant_kagawa_detail.csv"
)

print("list :", df_list.shape)
print("detail:", df_detail.shape)

df = pd.merge(
    df_list,
    df_detail,
    on="article_id",
    how="left"
)

print("merged:", df.shape)

print()

print(
    df["article_id"]
    .duplicated()
    .sum()
)

df.to_csv(
    "output/tenant_kagawa.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("saved tenant_kagawa.csv")

import pandas as pd

df = pd.read_csv(
    "output/tenant_kagawa.csv"
)

print(df.shape)

print(
    df["article_id"]
    .duplicated()
    .sum()
)