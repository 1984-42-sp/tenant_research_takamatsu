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

for tr in soup.select("tr"):

    cells = tr.find_all(["th", "td"])

    if len(cells) >= 2:

        key = cells[0].get_text(
            " ",
            strip=True
        )

        value = cells[1].get_text(
            " ",
            strip=True
        )

        print(
            f"{key} => {value}"
        )