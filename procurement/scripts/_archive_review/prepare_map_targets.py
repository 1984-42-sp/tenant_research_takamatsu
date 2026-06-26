from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_PATH = BASE_DIR / "output" / "master" / "supplier_locations.csv"
OUT_PATH = BASE_DIR / "output" / "master" / "supplier_map_targets.csv"

def main():
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig").fillna("")

    local_words = ["ローカル", "local", "Local", "LOCAL"]

    targets = df[
        df["local_or_online"].isin(local_words)
        & (df["address_candidate"].astype(str).str.strip() != "")
    ].copy()

    targets = targets[
        [
            "supplier_id",
            "source_category",
            "name",
            "type",
            "local_or_online",
            "address_candidate",
            "latitude",
            "longitude",
            "official_url",
            "google_maps_url",
            "main_items",
            "notes",
        ]
    ]

    targets.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print("[SAVE]", OUT_PATH)
    print("[ROWS]", len(targets))
    print(targets[["supplier_id", "name", "source_category", "address_candidate"]].head(50).to_string(index=False))

if __name__ == "__main__":
    main()