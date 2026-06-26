from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output" / "master"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXTRA_SUPPLIER_COLUMNS = [
    "product_tags",
    "fruit_tags",
    "coffee_tags",
    "dairy_tags",
    "tea_tags",
    "syrup_tags",
    "powder_tags",
    "cup_tags",
    "container_tags",
    "packaging_tags",
    "cleaning_tags",
    "machine_tags",
    "ice_tags",
    "other_tags",
    "strength_tags",
    "order_methods",
    "minimum_order",
    "minimum_amount",
    "delivery_area",
    "delivery_days",
    "payment_methods",
    "business_hours",
    "closed_days",
    "target_customers",
    "last_verified",
    "source_url",
    "info_confidence",
    "research_status",
    "notes_research",
]

def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig").fillna("")

def clean_note_text(value):
    text = str(value or "").strip()
    # 旧CSVで notes に混入した先頭の「可 / 可 / 」などのフラグ断片を除去する。
    while text.startswith("可 / "):
        text = text[4:].strip()
    return text


def normalize_minimum_order(value):
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    # 「可」は最小注文条件としては意味が曖昧なので、未調査扱いに寄せる。
    if text == "可":
        return "要確認"
    return text


def supplier_master():

    def first_existing(df, names, default=""):
        for name in names:
            if name in df.columns:
                return df[name]
        return default

    frames = []

    files = [
        ("fruit", DATA_DIR / "fruit" / "fruit_suppliers.csv"),
        ("coffee", DATA_DIR / "coffee" / "coffee_suppliers.csv"),
        ("consumables", DATA_DIR / "consumables" / "consumables_suppliers.csv"),
        ("materials", DATA_DIR / "materials" / "materials_suppliers.csv"),
        ("ice", DATA_DIR / "ice" / "ice_suppliers.csv"),
    ]

    for category, path in files:
        if not path.exists():
            continue

        df = read_csv(path)

        out = pd.DataFrame(index=df.index)

        out["supplier_id"] = first_existing(df, ["supplier_id", "id"])
        out["name"] = first_existing(df, ["name", "supplier_name", "名称"])
        out["type"] = first_existing(df, ["type", "category", "分類"])
        out["local_or_online"] = first_existing(df, ["local_or_online", "local_online", "オンライン区分"])
        out["official_url"] = first_existing(df, ["official_url", "url", "公式サイト"])
        out["google_maps_url"] = first_existing(df, ["google_maps_url", "map_url", "Google Maps"])
        out["main_items"] = first_existing(df, ["main_items", "bean_type", "items", "取扱商品"])
        out["delivery_available"] = first_existing(df, ["delivery_available", "delivery", "配送"])
        out["pickup_available"] = first_existing(df, ["pickup_available", "pickup", "受取"])
        out["notes"] = first_existing(df, ["notes", "備考", "特徴"])
        if hasattr(out["notes"], "apply"):
            out["notes"] = out["notes"].apply(clean_note_text)

        out["source_category"] = category
        for col in EXTRA_SUPPLIER_COLUMNS:
            out[col] = first_existing(df, [col], "")

        if category == "fruit":
            if "origin_selectable" in df.columns:
                out["fruit_tags"] = df["origin_selectable"]

            if "min_lot" in df.columns:
                out["minimum_order"] = df["min_lot"].apply(normalize_minimum_order)

            if "price_level" in df.columns:
                out["notes_research"] = df["price_level"]

            if "season_strength" in df.columns:
                out["strength_tags"] = df["season_strength"]

        if category == "coffee":
            def has_value(row, col):
                value = str(row.get(col, "")).strip()
                return value and value.lower() != "nan"

            def join_values(row, cols):
                return " / ".join(
                    str(row.get(c, "")).strip()
                    for c in cols
                    if has_value(row, c)
                )

            def join_flags(row, mapping):
                labels = []
                for col, label in mapping.items():
                    value = str(row.get(col, "")).strip()
                    if value == "○":
                        labels.append(label)
                    elif value and value.lower() != "nan":
                        labels.append(f"{label}:{value}")
                return " / ".join(labels)

            out["coffee_tags"] = df.apply(
                lambda r: join_values(r, ["bean_type", "roasting"]),
                axis=1,
            )

            out["strength_tags"] = df.apply(
                lambda r: join_flags(r, {
                    "espresso": "エスプレッソ",
                    "drip": "ドリップ",
                    "decaf": "デカフェ",
                    "organic": "オーガニック",
                    "fair_trade": "フェアトレード",
                    "machine_sales": "マシン販売",
                    "machine_lease": "マシンリース",
                    "machine_rental": "マシンレンタル",
                    "cups_available": "カップ対応",
                    "lids_available": "リッド対応",
                    "straws_available": "ストロー対応",
                    "oshibori_available": "おしぼり対応",
                    "other_consumables": "その他消耗品",
                    "opening_support": "開業支援",
                    "barista_training": "バリスタ研修",
                }),
                axis=1,
            )

            if "minimum_order" in df.columns:
                out["minimum_order"] = df["minimum_order"].apply(normalize_minimum_order)


            if "price_per_kg_yen" in df.columns:
                out["minimum_amount"] = df["price_per_kg_yen"].fillna("")    

        if category == "consumables":
            def flag_label(row, col, label):
                value = str(row.get(col, "")).strip()
                if value == "可":
                    return label
                if value and value.lower() != "nan":
                    return f"{label}:{value}"
                return ""

            def join_flags(row, mapping):
                labels = []
                for col, label in mapping.items():
                    v = flag_label(row, col, label)
                    if v:
                        labels.append(v)
                return " / ".join(labels)

            out["cup_tags"] = df.apply(
                lambda r: join_flags(r, {
                    "cups": "カップ",
                    "lids": "リッド",
                    "straws": "ストロー",
                }),
                axis=1,
            )

            out["packaging_tags"] = df.apply(
                lambda r: join_flags(r, {
                    "oshibori": "おしぼり",
                    "napkins": "ナプキン",
                    "takeout_bags": "テイクアウト袋",
                }),
                axis=1,
            )

            out["container_tags"] = df["main_items"].fillna("") if "main_items" in df.columns else ""

            # delivery_available は「配送可否」、delivery_area は「配送範囲」なので混ぜない。
            # consumables_suppliers.csv には配送範囲列がないため、delivery_area は空欄のままにする。
            out["delivery_area"] = ""

            if "min_lot" in df.columns:
                out["minimum_order"] = df["min_lot"].apply(normalize_minimum_order)

            out["strength_tags"] = out["cup_tags"].astype(str) + " / " + out["packaging_tags"].astype(str)
            out["strength_tags"] = out["strength_tags"].str.strip(" /")
    
        if category == "materials":

            def contains(text, keyword):
                return keyword in str(text)

            out["dairy_tags"] = df["main_items"].apply(
                lambda x: "乳製品" if any(
                    contains(x, k) for k in [
                        "牛乳", "生クリーム", "ホイップ",
                        "ヨーグルト", "チーズ", "バター"
                    ]
                ) else ""
            )

            out["syrup_tags"] = df["main_items"].apply(
                lambda x: "シロップ" if "シロップ" in str(x) else ""
            )

            out["powder_tags"] = df["main_items"].apply(
                lambda x: "パウダー" if "パウダー" in str(x) else ""
            )

            out["tea_tags"] = df["main_items"].apply(
                lambda x: "茶類" if any(
                    k in str(x) for k in [
                        "抹茶", "紅茶", "ほうじ茶", "茶"
                    ]
                ) else ""
            )

            out["other_tags"] = df["main_items"].fillna("")

            out["delivery_area"] = df["area"].fillna("")

            out["strength_tags"] = df["notes"].fillna("")

        if category == "ice":
            def flag_label(row, col, label):
                value = str(row.get(col, "")).strip()
                if value == "可":
                    return label
                if value and value.lower() != "nan":
                    return f"{label}:{value}"
                return ""

            def join_flags(row, mapping):
                labels = []
                for col, label in mapping.items():
                    v = flag_label(row, col, label)
                    if v:
                        labels.append(v)
                return " / ".join(labels)

            out["ice_tags"] = df.apply(
                lambda r: join_flags(r, {
                    "rock_ice_available": "ロックアイス",
                    "crush_ice_available": "クラッシュアイス",
                    "dry_ice_available": "ドライアイス",
                }),
                axis=1,
            )

            out["machine_tags"] = df.apply(
                lambda r: flag_label(r, "machine_available", "製氷機"),
                axis=1,
            )

            out["delivery_area"] = df["area"].fillna("")

            out["strength_tags"] = df["notes"].fillna("")

        frames.append(out)

    master = pd.concat(frames, ignore_index=True)
    master.to_csv(OUT_DIR / "supplier_master.csv", index=False, encoding="utf-8-sig")
    print("[SAVE] output/master/supplier_master.csv", master.shape)

def price_master():
    path = DATA_DIR / "prices" / "price_observations.csv"
    df = read_csv(path)

    df["unit_price_yen"] = pd.to_numeric(df["unit_price_yen"], errors="coerce")
    df["price_yen"] = pd.to_numeric(df["price_yen"], errors="coerce")

    base = df.dropna(subset=["unit_price_yen"]).copy()

    def joined_unique(s):
        vals = [str(x).strip() for x in s if str(x).strip()]
        return " / ".join(dict.fromkeys(vals))

    g = (
        base
        .groupby(["category", "item_name", "unit"], dropna=False)
        .agg(
            observation_count=("unit_price_yen", "count"),
            median_unit_price_yen=("unit_price_yen", "median"),
            mean_unit_price_yen=("unit_price_yen", "mean"),
            min_unit_price_yen=("unit_price_yen", "min"),
            max_unit_price_yen=("unit_price_yen", "max"),
            suppliers=("supplier", joined_unique),
            source_urls=("source_url", joined_unique),
            latest_checked_date=("checked_date", "max"),
        )
        .reset_index()
    )

    g.to_csv(OUT_DIR / "price_master.csv", index=False, encoding="utf-8-sig")
    print("[SAVE] output/master/price_master.csv", g.shape)

def fruit_price_master():
    path = DATA_DIR / "prices" / "fruit_price_observations.csv"
    df = read_csv(path)

    df["unit_price_yen"] = pd.to_numeric(df["unit_price_yen"], errors="coerce")
    df["price_yen"] = pd.to_numeric(df["price_yen"], errors="coerce")

    base = df.dropna(subset=["unit_price_yen"]).copy()

    def joined_unique(s):
        vals = [str(x).strip() for x in s if str(x).strip()]
        return " / ".join(dict.fromkeys(vals))

    g = (
        base
        .groupby(["item_name", "product_form", "unit"], dropna=False)
        .agg(
            observation_count=("unit_price_yen", "count"),
            median_unit_price_yen=("unit_price_yen", "median"),
            mean_unit_price_yen=("unit_price_yen", "mean"),
            min_unit_price_yen=("unit_price_yen", "min"),
            max_unit_price_yen=("unit_price_yen", "max"),
            suppliers=("supplier", joined_unique),
            source_urls=("source_url", joined_unique),
            latest_checked_date=("checked_date", "max"),
        )
        .reset_index()
    )

    g.to_csv(OUT_DIR / "fruit_price_master.csv", index=False, encoding="utf-8-sig")
    print("[SAVE] output/master/fruit_price_master.csv", g.shape)

def main():
    supplier_master()
    price_master()
    fruit_price_master()

if __name__ == "__main__":
    main()