from pathlib import Path
from bs4 import BeautifulSoup

DETAIL_DIR = Path(
    "data/html/takamatsu_housing/detail"
)

path = next(
    DETAIL_DIR.glob("*.html")
)

print(path.name)

html = path.read_text(
    encoding="utf-8",
    errors="ignore"
)

soup = BeautifulSoup(
    html,
    "lxml"
)

record = {}

for tr in soup.select("tr"):

    cells = tr.find_all(
        ["th", "td"]
    )

    if len(cells) < 2:
        continue

    key = cells[0].get_text(
        " ",
        strip=True
    )

    value = cells[1].get_text(
        " ",
        strip=True
    )

    if not key:
        continue

    record[key] = value

for k, v in record.items():
    print(f"{k} => {v}")

print()
print("特記事項:", record.get("特記事項"))