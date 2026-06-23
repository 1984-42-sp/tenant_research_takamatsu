from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

OUT_PATH = (
    BASE_DIR
    / "data"
    / "competitors"
    / "competitors_seed.csv"
)

COLUMNS = [
    "competitor_id",
    "store_name",
    "source",
    "genre",
    "address",
    "lat",
    "lng",
    "rating",
    "review_count",
    "business_hours",
    "closed_days",
    "url",
    "memo",
]


def main():
    OUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.DataFrame(columns=COLUMNS)

    df.to_csv(
        OUT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"[SAVE] {OUT_PATH}")


if __name__ == "__main__":
    main()