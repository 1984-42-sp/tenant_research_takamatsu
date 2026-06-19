import pandas as pd

LIST_PATH = "output/takamatsu_housing_list.csv"
DETAIL_PATH = "output/takamatsu_housing_detail.csv"
OUTPUT_PATH = "output/takamatsu_housing.csv"

df_list = pd.read_csv(
    LIST_PATH
)

df_detail = pd.read_csv(
    DETAIL_PATH
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
    "duplicated:",
    df["article_id"]
    .duplicated()
    .sum()
)

print()
print(
    df["飲食店可否"]
    .value_counts(dropna=False)
)

df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print()
print(f"saved: {OUTPUT_PATH}")