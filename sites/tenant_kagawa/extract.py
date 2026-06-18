from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://www.tenantkagawa.com"

HTML_DIR = Path(
    "data/html/tenant_kagawa"
)

records = []

for page_no in range(1, 6):

    path = HTML_DIR / f"list_page_{page_no}.html"

    print(f"loading {path}")

    html = path.read_text(
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    ids = soup.select(
        'input[id^="ID_ARTICLE_URL_"]'
    )

    names = soup.select(
        'input[id^="ID_ARTICLE_NAME_"]'
    )

    addresses = soup.select(
        'input[id^="ID_ADDRESS_"]'
    )

    rents = soup.select(
        'input[id^="ID_RENT_FEE_"]'
    )

    areas = soup.select(
        'input[id^="ID_CONTRACT_AREA_"]'
    )

    print(
        page_no,
        len(ids),
        len(names),
        len(addresses),
        len(rents),
        len(areas)
    )

    for i in range(len(ids)):

        article_id = ids[i]["value"]

        detail_url = (
            f"{BASE_URL}/article/search/{article_id}"
        )

        record = {
            "article_id": article_id,
            "name": names[i]["value"],
            "address": addresses[i]["value"],
            "rent_fee": rents[i]["value"],
            "contract_area": areas[i].get("value", ""),
            "detail_url": detail_url,
            "source_site": "tenant_kagawa"
        }

        records.append(record)

print()

print(
    "total records =",
    len(records)
)

print()

for row in records[:5]:

    print(row)

import pandas as pd

df_list = pd.DataFrame(records)

print()
print(df_list.shape)

print()
print(df_list.head())

df_list.to_csv(
    "output/tenant_kagawa_list.csv",
    index=False,
    encoding="utf-8-sig"
)

print()
print("saved")