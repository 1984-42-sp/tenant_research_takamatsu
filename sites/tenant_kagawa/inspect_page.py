from pathlib import Path
from bs4 import BeautifulSoup

html = Path(
    "data/html/tenant_kagawa/05_result.html"
).read_text(
    encoding="utf-8"
)

soup = BeautifulSoup(
    html,
    "lxml"
)

# URL
items = soup.select(
    'input[id^="ID_ARTICLE_URL_"]'
)

print("count =", len(items))

for item in items:
    print(item.get("value"))

# 家賃
rent_items = soup.select(
    'input[id^="ID_RENT_FEE_"]'
)

print(
    "rent count =",
    len(rent_items)
)

for item in rent_items[:3]:
    print(item.get("value"))

# 面積
area_items = soup.select(
    'input[id^="ID_CONTRACT_AREA_"]'
)

print(
    "area count =",
    len(area_items)
)

for item in area_items[:3]:
    print(item.get("value"))

# 所在地

address_items = soup.select(
    'input[id^="ID_ADDRESS_"]'
)

print(
    "address count =",
    len(address_items)
)

for item in address_items[:3]:
    print(item.get("value"))


# 物件名

name_items = soup.select(
    'input[id^="ID_ARTICLE_NAME_"]'
)

print(
    "name count =",
    len(name_items)
)

for item in name_items[:3]:
    print(item.get("value"))

#特定
print("\n===== pagination links =====\n")

for a in soup.find_all("a"):

    text = a.get_text(strip=True)

    href = a.get("href")

    if text:

        print(
            f"text={text} | href={href}"
        )

forms = soup.find_all("form")

print("form count =", len(forms))

for i, form in enumerate(forms):

    print("\n====================")
    print("FORM", i)
    print("====================")

    print(
        form.get("action")
    )

    from pathlib import Path
from bs4 import BeautifulSoup

for page_no in range(1, 6):

    path = Path(
        f"data/html/tenant_kagawa/list_page_{page_no}.html"
    )

    soup = BeautifulSoup(
        path.read_text(encoding="utf-8"),
        "lxml"
    )

    ids = soup.select(
        'input[id^="ID_ARTICLE_URL_"]'
    )

    print(
        f"page {page_no} = {len(ids)}"
    )