from pathlib import Path

import pandas as pd

LIST_CSV = Path("output/mcrea/mcrea_list.csv")
DETAIL_CSV = Path("output/mcrea/mcrea_detail.csv")

OUT_CSV = Path("output/mcrea/mcrea.csv")


def main():
    list_df = pd.read_csv(LIST_CSV)
    detail_df = pd.read_csv(DETAIL_CSV)

    print("list   :", list_df.shape)
    print("detail :", detail_df.shape)

    merged = list_df.merge(
        detail_df,
        left_on="detail_url",
        right_on="detail_url",
        how="left",
        suffixes=("_list", "_detail"),
    )

    merged.to_csv(
        OUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print("merged :", merged.shape)
    print("saved  :", OUT_CSV)


if __name__ == "__main__":
    main()