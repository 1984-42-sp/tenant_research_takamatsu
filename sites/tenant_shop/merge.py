from pathlib import Path

import pandas as pd

DETAIL_CSV = Path("output/tenant_shop/tenant_shop_detail.csv")
OUT_CSV = Path("output/tenant_shop/tenant_shop.csv")


def main():
    df = pd.read_csv(DETAIL_CSV)

    print("detail :", df.shape)

    df.to_csv(
        OUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print("merged :", df.shape)
    print("saved  :", OUT_CSV)


if __name__ == "__main__":
    main()