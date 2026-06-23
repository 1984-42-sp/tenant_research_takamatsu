from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata


DETAIL_DIR = Path("data/html/tenant_kagawa/detail")
OUT_DIR = Path("output/tenant_kagawa")
OUT_CSV = OUT_DIR / "tenant_kagawa_detail.csv"


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
    "PageUp",
    "PageDown",
}


def normalize_key(value):
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", "", text)
    text = text.strip()

    aliases = {
        "賃料": "賃料",
        "賃料(税込)": "賃料",
        "賃料（税込）": "賃料",
        "家賃": "賃料",
    }

    return aliases.get(text, text)


def clean_value(value):
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pairs_from_tr(tr):
    cells = tr.find_all(["th", "td"])

    pairs = []

    i = 0
    while i < len(cells) - 1:
        if cells[i].name != "th":
            i += 1
            continue

        key = normalize_key(
            cells[i].get_text(" ", strip=True)
        )

        value = clean_value(
            cells[i + 1].get_text(" ", strip=True)
        )

        if key and key not in IGNORE_KEYS:
            pairs.append((key, value))

        i += 2

    return pairs


def main():
    records = []

    files = sorted(DETAIL_DIR.glob("*.html"))

    print(f"files: {len(files)}")

    for file in files:
        article_id = file.stem

        html = file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        soup = BeautifulSoup(html, "lxml")

        record = {
            "article_id": article_id
        }

        for tr in soup.select("tr"):
            for key, value in extract_pairs_from_tr(tr):
                if key in record and record[key] != value:
                    record[f"{key}_2"] = value
                else:
                    record[key] = value

        records.append(record)

    df = pd.DataFrame(records)

    print(df.shape)
    print(df.columns.tolist())

    print()
    print("賃料 column exists:", "賃料" in df.columns)

    if "賃料" in df.columns:
        print()
        print(df[["article_id", "賃料"]].head(20))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print(f"saved detail csv: {OUT_CSV}")


if __name__ == "__main__":
    main()