from pathlib import Path

import pandas as pd

LIST_CSV = Path(
    "output/uemura_re/uemura_re_list.csv"
)

DETAIL_CSV = Path(
    "output/uemura_re/uemura_re_detail.csv"
)

OUT_CSV = Path(
    "output/uemura_re/uemura_re.csv"
)


def main():
    list_df = pd.read_csv(LIST_CSV)
    detail_df = pd.read_csv(DETAIL_CSV)

    print(f"list  : {list_df.shape}")
    print(f"detail: {detail_df.shape}")

    merged = detail_df.merge(
        list_df,
        on=["site", "category", "detail_url"],
        how="left",
        suffixes=("", "_list"),
    )

    duplicated = merged.duplicated(subset=["detail_url"]).sum()
    print(f"duplicated detail_url: {duplicated}")

    merged.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"merged: {merged.shape}")
    print(f"saved : {OUT_CSV}")


if __name__ == "__main__":
    main()