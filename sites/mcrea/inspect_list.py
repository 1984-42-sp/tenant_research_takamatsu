from pathlib import Path
from bs4 import BeautifulSoup

HTML_DIR = Path("data/html/mcrea")


def inspect_file(path: Path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

    print("=" * 80)
    print(path)
    print("title:", soup.title.get_text(strip=True) if soup.title else None)

    text = soup.get_text(" ", strip=True)
    for keyword in ["件中", "件を表示", "飲食店可", "高松市"]:
        print(f"{keyword}:", keyword in text)

    detail_links = soup.select("a[href*='detail']")
    object_name_links = soup.select("p.object-name a[href*='detail']")

    print("a[href*='detail'] count:", len(detail_links))
    print("p.object-name a[href*='detail'] count:", len(object_name_links))

    seen = set()
    for i, a in enumerate(object_name_links[:40], start=1):
        href = a.get("href")
        name = a.get_text(" ", strip=True)

        if href in seen:
            continue
        seen.add(href)

        print("-" * 60)
        print(i)
        print("name:", name)
        print("href:", href)

        parent = a.find_parent()
        if parent:
            print("parent tag:", parent.name)
            print("parent class:", parent.get("class"))
            print("parent text:", parent.get_text(" ", strip=True)[:300])


def main():
    files = sorted(HTML_DIR.glob("list_page_*.html"))
    print(f"files: {len(files)}")

    for path in files:
        inspect_file(path)


if __name__ == "__main__":
    main()