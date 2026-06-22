from pathlib import Path

import pandas as pd


OUT_DIR = Path("output/takamatsu_housing")

LIST_PATH = OUT_DIR / "takamatsu_housing_list.csv"
DETAIL_PATH = OUT_DIR / "takamatsu_housing_detail.csv"
OUT_CSV = OUT_DIR / "takamatsu_housing.csv"


def main():
    df_list = pd.read_csv(LIST_PATH)
    df_detail = pd.read_csv(DETAIL_PATH)

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

    check_df = pd.read_csv(OUT_CSV)

    print(check_df.shape)
    print(
        check_df["article_id"]
        .duplicated()
        .sum()
    )


if __name__ == "__main__":
    main()