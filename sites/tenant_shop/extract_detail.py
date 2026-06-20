from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

import selectors

DETAIL_DIR = Path("data/html/tenant_shop/detail")
OUT_PATH = Path("output/tenant_shop/tenant_shop_detail.csv")


def clean(text: str) -> str:
    return " ".join(str(text).split()).strip()


def get_next_value(lines, key):
    for i, line in enumerate(lines):
        if line == key and i + 1 < len(lines):
            return lines[i + 1]
    return None


def main():
    rows = []

    for path in sorted(DETAIL_DIR.glob("*.html")):
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

        lines = [
            clean(line)
            for line in soup.get_text("\n", strip=True).splitlines()
        ]
        lines = [line for line in lines if line]

        title = soup.title.get_text(strip=True) if soup.title else None
        h1 = soup.select_one("h1")

        row = {
            "site": selectors.SITE_LABEL,
            "category": "賃貸店舗・事務所",
            "物件名": clean(h1.get_text(" ", strip=True)) if h1 else None,
            "ページタイトル": title,
            "detail_url": selectors.DETAIL_URLS[0],
            "html_file": str(path),
            "物件No": None,
            "所在地": None,
            "交通": None,
            "賃料": None,
            "坪単価": None,
            "管理費": get_next_value(lines, "管理費"),
            "保証金": None,
            "解約引": None,
            "敷金": None,
            "礼金": None,
            "建物/専有面積": None,
            "土地面積": get_next_value(lines, "土地面積"),
            "築年月": get_next_value(lines, "築年月"),
            "駐車場": get_next_value(lines, "駐車場"),
            "所在階": get_next_value(lines, "所在階"),
            "地上階数": None,
            "地下階数": None,
            "取引": get_next_value(lines, "取引"),
            "物件登録日": get_next_value(lines, "物件登録日"),
            "情報更新日": get_next_value(lines, "情報更新日"),
            "備考": None,
        }

        for i, line in enumerate(lines):
            if line.startswith("物件No."):
                row["物件No"] = line.replace("物件No.", "").strip()

                if i + 2 < len(lines):
                    row["所在地"] = lines[i + 2]

            if "瓦町駅" in line:
                row["交通"] = line

            if line == "賃料" and i + 3 < len(lines):
                row["賃料"] = clean(f"{lines[i + 1]}{lines[i + 2]}{lines[i + 3]}")

            if "坪単価" in line:
                row["坪単価"] = line

            if line == "敷金" and i + 1 < len(lines):
                row["敷金"] = lines[i + 1]

            if line == "礼金" and i + 1 < len(lines):
                row["礼金"] = lines[i + 1]

            if line == "建物/専有" and i + 4 < len(lines):
                row["建物/専有面積"] = clean(
                    f"{lines[i + 2]}{lines[i + 3]} {lines[i + 4]}"
                )

            if line == "地上階数" and i + 1 < len(lines):
                row["地上階数"] = lines[i + 1]

            if line == "地下階数" and i + 1 < len(lines):
                row["地下階数"] = lines[i + 1]

        remarks = []
        for keyword in ["パールコート１０２号", "飲食可", "大型コインパーキング", "スケルトン", "テナント　店舗"]:
            if keyword in lines:
                remarks.append(keyword)

        row["備考"] = " / ".join(remarks)

        rows.append(row)

    df = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"extracted: {len(df)}")
    print(f"expected : {selectors.EXPECTED_TOTAL_COUNT}")
    print(f"saved    : {OUT_PATH}")
    print(f"columns  : {len(df.columns)}")

    if len(df) != selectors.EXPECTED_TOTAL_COUNT:
        raise ValueError("詳細取得件数が想定件数と一致しません")


if __name__ == "__main__":
    main()