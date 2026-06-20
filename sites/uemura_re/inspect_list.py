from pathlib import Path
from bs4 import BeautifulSoup

HTML_PATH = Path("data/html/uemura_re/list_page_1.html")

def main():
    soup = BeautifulSoup(HTML_PATH.read_text(encoding="utf-8"), "lxml")

    print("title:", soup.title.get_text(strip=True) if soup.title else None)
    print("a[href*='detail'] count:", len(soup.select("a[href*='detail']")))

    for i, a in enumerate(soup.select("a[href*='detail']")[:20], start=1):
        text = a.get_text(" ", strip=True)
        href = a.get("href")
        print("-" * 60)
        print(i)
        print("text:", text[:200])
        print("href:", href)

        parent = a.find_parent()
        if parent:
            print("parent tag:", parent.name)
            print("parent class:", parent.get("class"))
            print("parent text:", parent.get_text(" ", strip=True)[:500])


if __name__ == "__main__":
    main()