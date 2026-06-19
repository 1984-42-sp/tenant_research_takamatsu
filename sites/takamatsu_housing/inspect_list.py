from pathlib import Path
from bs4 import BeautifulSoup

path = Path(
    "data/html/takamatsu_housing/list_page_1.html"
)

html = path.read_text(
    encoding="utf-8"
)

soup = BeautifulSoup(
    html,
    "lxml"
)

for a in soup.find_all("a", href=True):

    href = a["href"]

    if "/kasi-tenpo/detail-" in href:

        print("href:", href)
        print("text:", a.get_text(" ", strip=True))

        parent = a

        for i in range(1, 8):

            parent = parent.parent

            print()
            print("=" * 80)
            print(f"PARENT {i}")
            print("=" * 80)
            print(parent.name)
            print(parent.get("class"))
            print(parent.get_text(" ", strip=True)[:1500])

        break