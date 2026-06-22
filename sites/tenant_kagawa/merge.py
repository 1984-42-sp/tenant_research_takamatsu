import pandas as pd

from pathlib import Path

OUT_CSV = Path(
    "output/tenant_kagawa/tenant_kagawa.csv"
)

df_list = pd.read_csv(
    "output/tenant_kagawa/tenant_kagawa.csv"
)

df_detail = pd.read_csv(
    "output/tenant_kagawa/tenant_kagawa_detail.csv"
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

from pathlib import Path

OUT_CSV = Path(
    "output/tenant_kagawa/tenant_kagawa.csv"
)

OUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

print()
print(f"saved {OUT_CSV}")

df = pd.read_csv(
    OUT_CSV
)

print(df.shape)

print(
    df["article_id"]
    .duplicated()
    .sum()
)

print(df.shape)

print(
    df["article_id"]
    .duplicated()
    .sum()
)