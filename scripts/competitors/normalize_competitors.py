from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
IN_PATH = BASE_DIR / "data" / "competitors" / "competitors_seed.csv"
OUT_PATH = BASE_DIR / "data" / "competitors" / "competitors_normalized.csv"

COLUMNS = [
    "competitor_id", "store_name", "source", "genre", "address",
    "lat", "lng", "rating", "review_count",
    "business_hours", "closed_days", "url", "memo",
]

def text(v):
    if pd.isna(v):
        return ""
    s = str(v).strip().replace("\u3000", " ")
    return re.sub(r"\s+", " ", s)

def address(v):
    s = text(v)
    s = s.replace("香川県", "")
    for ch in ["－", "ー", "―", "–", "—"]:
        s = s.replace(ch, "-")
    s = re.sub(r"-+", "-", s)
    if s and not s.startswith("高松市"):
        s = "高松市" + s
    return s

def num(v):
    s = text(v).replace(",", "")
    return re.sub(r"[^0-9.]", "", s)

def main():
    df = pd.read_csv(IN_PATH, dtype=str).fillna("")

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS].copy()

    for col in ["store_name", "source", "genre", "business_hours", "closed_days", "url", "memo"]:
        df[col] = df[col].apply(text)

    df["address"] = df["address"].apply(address)

    for col in ["lat", "lng", "rating", "review_count"]:
        df[col] = df[col].apply(num)

    df = df[df["store_name"] != ""].copy()
    df = df.drop_duplicates(subset=["store_name", "address", "source"]).reset_index(drop=True)

    df["competitor_id"] = [
        cid if cid else f"C{i+1:05d}"
        for i, cid in enumerate(df["competitor_id"])
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[LOAD] {IN_PATH}: {len(df)} rows")
    print(f"[SAVE] {OUT_PATH}")

if __name__ == "__main__":
    main()