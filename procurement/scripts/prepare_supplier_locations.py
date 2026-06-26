from pathlib import Path
import pandas as pd
import re
from urllib.parse import unquote

BASE_DIR = Path(__file__).resolve().parents[1]
MASTER_PATH = BASE_DIR / "output" / "master" / "supplier_master.csv"
OUT_PATH = BASE_DIR / "output" / "master" / "supplier_locations.csv"

def extract_query_from_google_maps(url: str) -> str:
    if not isinstance(url, str) or "query=" not in url:
        return ""
    q = url.split("query=", 1)[1]
    q = q.split("&", 1)[0]
    return unquote(q).replace("+", " ").strip()

def extract_address_from_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    patterns = [
        r"(高松市[^。,\"]+)",
        r"(香川県[^。,\"]+)",
        r"(丸亀市[^。,\"]+)",
        r"(坂出市[^。,\"]+)",
        r"(綾歌郡[^。,\"]+)",
        r"(木田郡[^。,\"]+)",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()

    return ""

def normalize_address_candidate(row):
    text = str(row.get("address_candidate", "")).strip()
    name = str(row.get("name", "")).strip()
    notes = str(row.get("notes", "")).strip()

    market_keywords = [
        "中央卸売市場",
        "市場内",
        "青果仲卸",
        "場内業者",
        "青果部仲卸",
        "うみまち商店街",
    ]

    if any(k in text for k in market_keywords) or any(k in notes for k in market_keywords):
        return "高松市朝日町3-8-25"

    replacements = {
        "高松市兵庫町の老舗果実専門店": "高松市兵庫町7-3",
        "高松市南新町の果物店": "高松市南新町4-4",
        "高松市鬼無町": "高松市鬼無町佐料20-1",
        "丸亀市だが大型産直": "丸亀市飯山町西坂元655-1",
    }

    if text in replacements:
        return replacements[text]

    return text

def main():
    df = pd.read_csv(MASTER_PATH, encoding="utf-8-sig").fillna("")

    df["map_query"] = df["google_maps_url"].apply(extract_query_from_google_maps)

    if "address" not in df.columns:
        df["address"] = ""

    df["address_candidate"] = df.apply(
        lambda r: r["address"]
        or extract_address_from_text(r.get("notes", ""))
        or r["map_query"],
        axis=1,
    )

    df["address_candidate"] = df.apply(normalize_address_candidate, axis=1)

    df["latitude"] = ""
    df["longitude"] = ""
    df["map_available"] = df["address_candidate"].apply(lambda x: "yes" if x else "no")

    cols = [
        "supplier_id",
        "source_category",
        "name",
        "type",
        "local_or_online",
        "address_candidate",
        "latitude",
        "longitude",
        "map_available",
        "official_url",
        "google_maps_url",
        "main_items",
        "notes",
    ]

    out = df[cols]
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print("[SAVE]", OUT_PATH)
    print(out["map_available"].value_counts(dropna=False))
    print(out.head(30).to_string(index=False))

if __name__ == "__main__":
    main()