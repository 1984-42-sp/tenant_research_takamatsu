from pathlib import Path
from playwright.sync_api import sync_playwright

from fetch_search import run_search


SAVE_DIR = Path("data/html/tenant_kagawa")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def save_html(page, filename):

    path = SAVE_DIR / filename

    path.write_text(
        page.content(),
        encoding="utf-8"
    )

    print(f"saved -> {path}")


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        #
        # 高松市検索
        #
        run_search(page)

        #
        # 1ページ目保存
        #
        save_html(
            page,
            "list_page_1.html"
        )

        #
        # 2～5ページ
        #
        for page_no in range(2, 6):

            url = (
                "https://www.tenantkagawa.com"
                f"/article/search/result?sf=&st=desc&page={page_no}"
            )

            print(
                f"page {page_no}"
            )

            page.goto(
                url,
                wait_until="networkidle"
            )

            save_html(
                page,
                f"list_page_{page_no}.html"
            )

        browser.close()


if __name__ == "__main__":
    main()