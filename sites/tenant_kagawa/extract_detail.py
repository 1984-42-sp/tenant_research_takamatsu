from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata


def normalize_key(value):
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", "", text)
    return text.strip()

DETAIL_DIR = Path(
    "data/html/tenant_kagawa/detail"
)

IGNORE_KEYS = {
    "",
    "←",
    "→",
    "↑",
    "↓",
    "+",
    "-",
    "Home",
    "End",
    "Page Up",
    "Page Down",
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

        key = normalize_key(
            cells[0].get_text(
                " ",
                strip=True
            )
        )

        value = cells[1].get_text(
            " ",
            strip=True
        )

        if key in IGNORE_KEYS:
            continue

        record[key] = value

    records.append(record)

df = pd.DataFrame(records)

print(df.shape)

print(df.columns.tolist())

print()

for col in sorted(df.columns):
    print(col)

    print()
print(df.isna().sum())

Path("output/tenant_kagawa").mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    "output/tenant_kagawa/tenant_kagawa_detail.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("saved detail csv")