from pathlib import Path
from bs4 import BeautifulSoup

path = Path(
    "data/html/tenant_kagawa/detail/00002636.html"
)

html = path.read_text(
    encoding="utf-8"
)

soup = BeautifulSoup(
    html,
    "lxml"
)

tables = soup.find_all("table")

print(f"table数: {len(tables)}")

for i, table in enumerate(tables):

    print()
    print("=" * 50)
    print(f"TABLE {i}")
    print("=" * 50)

    text = table.get_text(
        "\n",
        strip=True
    )

    print(text[:1000])