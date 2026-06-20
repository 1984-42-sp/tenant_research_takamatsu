from pathlib import Path
from bs4 import BeautifulSoup

DETAIL_DIR = Path("data/html/uemura_re/detail")


def main():
    files = sorted(DETAIL_DIR.glob("*.html"))
    print(f"files: {len(files)}")

    path = files[0]
    print(f"inspect: {path}")

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

    print("title:", soup.title.get_text(strip=True) if soup.title else None)

    print("\n[h1/h2/h3]")
    for tag in soup.select("h1, h2, h3")[:20]:
        print(tag.name, tag.get("class"), tag.get_text(" ", strip=True))

    print("\n[table rows]")
    for i, tr in enumerate(soup.select("tr")[:80], start=1):
        cells = [c.get_text(" ", strip=True) for c in tr.select("th, td")]
        if cells:
            print(i, cells)

    print("\n[detail text sample]")
    main_text = soup.get_text("\n", strip=True)
    for line in main_text.splitlines()[:120]:
        print(line)


if __name__ == "__main__":
    main()