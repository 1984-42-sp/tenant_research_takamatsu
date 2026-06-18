from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


HTML_DIR = Path(
    "data/html/tenant_kagawa"
)

DETAIL_DIR = Path(
    "data/html/tenant_kagawa/detail"
)

DETAIL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def get_article_ids():

    article_ids = []

    for page_no in range(1, 6):

        path = (
            HTML_DIR /
            f"list_page_{page_no}.html"
        )

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

        for tag in ids:

            article_ids.append(
                tag["value"]
            )

    return article_ids

def save_html(page, article_id):

    path = (
        DETAIL_DIR /
        f"{article_id}.html"
    )

    path.write_text(
        page.content(),
        encoding="utf-8"
    )

    print(
        f"saved -> {path}"
    )

def main():

    article_ids = get_article_ids()

    print(
        "found article ids =",
        len(article_ids)
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        for article_id in article_ids:

            url = (
                "https://www.tenantkagawa.com"
                f"/article/search/{article_id}"
            )

            print(url)

            page.goto(
                url,
                wait_until="networkidle"
            )

            save_html(
                page,
                article_id
            )

        browser.close()


if __name__ == "__main__":
    main()