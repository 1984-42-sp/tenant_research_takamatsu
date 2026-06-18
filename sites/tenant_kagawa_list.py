from pathlib import Path
from playwright.sync_api import sync_playwright


URL = "https://www.tenantkagawa.com/article/search/result"

SAVE_PATH = Path(
    "data/html/tenant_kagawa_result_page1.html"
)


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            URL,
            wait_until="networkidle"
        )

        SAVE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        SAVE_PATH.write_text(
            page.content(),
            encoding="utf-8"
        )

        print(
            f"saved: {SAVE_PATH}"
        )

        input("Enterで終了")

        browser.close()


if __name__ == "__main__":
    main()