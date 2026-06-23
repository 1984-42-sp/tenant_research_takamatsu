from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_PATH = BASE_DIR / "data" / "competitors" / "raw" / "tabelog_cafe_competitors.csv"
OUT_PATH = BASE_DIR / "data" / "competitors" / "competitors_seed.csv"


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
    df = pd.read_csv(RAW_PATH, dtype=str).fillna("")

    out = pd.DataFrame()
    out["competitor_id"] = [f"TBL{i + 1:05d}" for i in range(len(df))]
    out["store_name"] = df["store_name"].str.strip()
    out["source"] = "tabelog"
    out["genre"] = df["genre"].str.strip()
    out["address"] = df["address"].str.strip()
    out["lat"] = ""
    out["lng"] = ""
    out["rating"] = df.get("rating", "").astype(str).str.strip().replace({"nan": ""})
    out["review_count"] = (
        df["review_count"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
    )
    out["business_hours"] = ""
    out["closed_days"] = ""
    out["url"] = df["url"].str.strip()
    out["memo"] = "source=tabelog; import_method=script"

    out = out[COLUMNS]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"[LOAD] {RAW_PATH}: {len(df)} rows")
    print(f"[SAVE] {OUT_PATH}: {len(out)} rows")


if __name__ == "__main__":
    main()