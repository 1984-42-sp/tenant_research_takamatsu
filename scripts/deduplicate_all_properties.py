from pathlib import Path
import re
import unicodedata
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "all_properties" / "all_properties.csv"

OUT_DEDUP = BASE_DIR / "output" / "all_properties" / "all_properties_deduplicated.csv"
OUT_CANDIDATES = BASE_DIR / "output" / "all_properties" / "all_properties_duplicate_candidates.csv"


def normalize_text(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.lower()
    text = text.replace("　", " ")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"貸店舗|貸事務所|店舗|事務所|一部|賃貸|テナント|\(|\)|（|）", "", text)
    return text.strip()


def normalize_address(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("香川県", "")
    text = text.replace("高松市", "")
    text = text.replace("　", "")
    text = re.sub(r"\s+", "", text)
    text = text.replace("−", "-").replace("－", "-").replace("―", "-")
    return text.strip()


def to_float(value):
    if pd.isna(value):
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace(",", "")
    m = re.search(r"\d+(\.\d+)?", text)
    if not m:
        return None
    return float(m.group())


def similar_number(a, b, tolerance_rate=0.03, tolerance_abs=0.3):
    if a is None or b is None:
        return False
    return abs(a - b) <= max(tolerance_abs, max(abs(a), abs(b)) * tolerance_rate)


def same_rent(a, b):
    if a is None or b is None:
        return False
    return abs(a - b) <= max(3000, max(abs(a), abs(b)) * 0.03)


def build_keys(df):
    df = df.copy()

    df["_name_norm"] = df["物件名"].apply(normalize_text) if "物件名" in df.columns else ""
    df["_addr_norm"] = df["所在地"].apply(normalize_address) if "所在地" in df.columns else ""
    area_col = "坪数_補正" if "坪数_補正" in df.columns else "坪数数値"
    rent_col = "家賃_円" if "家賃_円" in df.columns else "家賃数値"

    df["_area_num"] = df[area_col].apply(to_float) if area_col in df.columns else None
    df["_rent_num"] = df[rent_col].apply(to_float) if rent_col in df.columns else None

    return df


def is_auto_duplicate(base, other):
    if base["_addr_norm"] == "" or other["_addr_norm"] == "":
        return False

    same_address = base["_addr_norm"] == other["_addr_norm"]
    same_area = similar_number(base["_area_num"], other["_area_num"])
    rent_match = same_rent(base["_rent_num"], other["_rent_num"])

    # 所在地・坪数・家賃が一致するなら、物件名が多少違っても同一物件扱い
    return same_address and same_area and rent_match


def is_candidate_duplicate(base, other):
    if base["_addr_norm"] == "" or other["_addr_norm"] == "":
        return False

    same_address = base["_addr_norm"] == other["_addr_norm"]

    if not same_address:
        return False

    same_area = similar_number(base["_area_num"], other["_area_num"], tolerance_rate=0.08, tolerance_abs=1.0)
    rent_match = same_rent(base["_rent_num"], other["_rent_num"])

    # 同住所で、面積または家賃が近いものだけ要確認候補にする
    return same_area or rent_match


def choose_representative(group):
    # 情報量が多い行を代表にする
    best_idx = None
    best_score = -1

    for idx, row in group.iterrows():
        score = 0
        for value in row.values:
            if not pd.isna(value) and str(value).strip() != "":
                score += 1

        if "詳細URL" in group.columns and str(row.get("詳細URL", "")).strip():
            score += 3

        if "掲載サイト" in group.columns and str(row.get("掲載サイト", "")).strip():
            score += 1

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def main():
    df = pd.read_csv(INPUT_CSV)
    df = build_keys(df)

    used = set()
    representative_indices = []
    candidate_rows = []

    for i, base in df.iterrows():
        if i in used:
            continue

        auto_group = [i]
        candidate_group = []

        for j in range(i + 1, len(df)):
            if j in used:
                continue

            other = df.loc[j]

            if is_auto_duplicate(base, other):
                auto_group.append(j)
            elif is_candidate_duplicate(base, other):
                candidate_group.append(j)

        group_df = df.loc[auto_group]
        rep_idx = choose_representative(group_df)
        representative_indices.append(rep_idx)

        for idx in auto_group:
            if idx != rep_idx:
                used.add(idx)
                candidate_rows.append({
                    "判定": "自動重複削除",
                    "代表index": rep_idx,
                    "重複index": idx,
                    "代表物件名": df.loc[rep_idx].get("物件名", ""),
                    "重複物件名": df.loc[idx].get("物件名", ""),
                    "代表所在地": df.loc[rep_idx].get("所在地", ""),
                    "重複所在地": df.loc[idx].get("所在地", ""),
                    "代表家賃": df.loc[rep_idx].get("家賃", ""),
                    "重複家賃": df.loc[idx].get("家賃", ""),
                    "代表坪数": df.loc[rep_idx].get("坪数数値", df.loc[rep_idx].get("坪数_補正", "")),
                    "重複坪数": df.loc[idx].get("坪数数値", df.loc[idx].get("坪数_補正", "")),
                    "代表サイト": df.loc[rep_idx].get("掲載サイト", ""),
                    "重複サイト": df.loc[idx].get("掲載サイト", ""),
                    "代表URL": df.loc[rep_idx].get("詳細URL", ""),
                    "重複URL": df.loc[idx].get("詳細URL", ""),
                })

        for idx in candidate_group:
            candidate_rows.append({
                "判定": "要確認候補",
                "代表index": i,
                "重複index": idx,
                "代表物件名": df.loc[i].get("物件名", ""),
                "重複物件名": df.loc[idx].get("物件名", ""),
                "代表所在地": df.loc[i].get("所在地", ""),
                "重複所在地": df.loc[idx].get("所在地", ""),
                "代表家賃": df.loc[i].get("家賃", ""),
                "重複家賃": df.loc[idx].get("家賃", ""),
                "代表坪数": df.loc[i].get("坪数数値", df.loc[i].get("坪数_補正", "")),
                "重複坪数": df.loc[idx].get("坪数数値", df.loc[idx].get("坪数_補正", "")),
                "代表サイト": df.loc[i].get("掲載サイト", ""),
                "重複サイト": df.loc[idx].get("掲載サイト", ""),
                "代表URL": df.loc[i].get("詳細URL", ""),
                "重複URL": df.loc[idx].get("詳細URL", ""),
            })

        used.add(i)

    dedup_df = df.loc[representative_indices].copy()
    dedup_df = dedup_df.drop(columns=[c for c in dedup_df.columns if c.startswith("_")])

    candidates_df = pd.DataFrame(candidate_rows)

    dedup_df.to_csv(OUT_DEDUP, index=False, encoding="utf-8-sig")
    candidates_df.to_csv(OUT_CANDIDATES, index=False, encoding="utf-8-sig")

    print(f"[LOAD] {INPUT_CSV}")
    print(f"[SAVE] {OUT_DEDUP}")
    print(f"[SAVE] {OUT_CANDIDATES}")
    print(f"[ORIGINAL] {len(df)}")
    print(f"[DEDUP] {len(dedup_df)}")
    print(f"[REMOVED] {len(df) - len(dedup_df)}")
    print(f"[CANDIDATES] {len(candidates_df)}")

    if not candidates_df.empty:
        print("\n[CANDIDATE SUMMARY]")
        print(candidates_df["判定"].value_counts().to_string())


if __name__ == "__main__":
    main()