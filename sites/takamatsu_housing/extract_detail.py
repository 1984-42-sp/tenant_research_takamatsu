from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

DETAIL_DIR = Path(
    "data/html/takamatsu_housing/detail"
)

OUTPUT_PATH = Path(
    "output/takamatsu_housing_detail.csv"
)

IGNORE_KEYS = {
    "",
    "200万円以下の金額",
    "200万円を超え400万円以下の金額",
    "400万円を超える金額",
}

records = []

for file in DETAIL_DIR.glob("*.html"):

    article_id = file.stem

    html = file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    record = {
        "article_id": article_id
    }

    for tr in soup.select("tr"):

        cells = tr.find_all(
            ["th", "td"]
        )

        if len(cells) < 2:
            continue

        key = cells[0].get_text(
            " ",
            strip=True
        )

        value = cells[1].get_text(
            " ",
            strip=True
        )

        if key in IGNORE_KEYS:
            continue

        record[key] = value

    special_note = str(
        record.get("特記事項", "")
    )

    if "飲食店不可" in special_note:
        record["飲食店可否"] = "不可"
    elif (
        "飲食店可" in special_note
        or "軽飲食" in special_note
        or "重飲食" in special_note
    ):
        record["飲食店可否"] = "可"
    else:
        record["飲食店可否"] = "不明"

    records.append(record)

df = pd.DataFrame(records)

print(df.shape)

print()
print(df.columns.tolist())

print()
print(
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