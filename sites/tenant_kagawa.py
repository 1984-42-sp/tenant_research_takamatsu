from pathlib import Path
from playwright.sync_api import sync_playwright


OUTPUT_FILE = Path("data/html/tenant_kagawa_top.html")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            "https://www.tenantkagawa.com/",
            wait_until="networkidle"
        )

        html = page.content()

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        OUTPUT_FILE.write_text(
            html,
            encoding="utf-8"
        )

        print(
            f"saved -> {OUTPUT_FILE}"
        )

        input("Enterで終了")

        browser.close()


if __name__ == "__main__":
    main()