from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.tenantkagawa.com"

SAVE_DIR = Path("data/html/tenant_kagawa")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def save_html(page, filename):

    path = SAVE_DIR / filename

    path.write_text(
        page.content(),
        encoding="utf-8"
    )

    print(f"saved -> {path}")


def run_search(page):

    print("トップページ取得")

    page.goto(
        BASE_URL,
        wait_until="networkidle"
    )

    save_html(
        page,
        "01_top.html"
    )

    print("店舗検索タブ")

    page.click(
        'a[href="#search_add"]'
    )

    page.wait_for_timeout(1000)

    save_html(
        page,
        "02_tab.html"
    )

    print("住所から選択")

    page.click(
        'a[title="住所から選択"]'
    )

    page.wait_for_timeout(3000)

    save_html(
        page,
        "03_address_modal.html"
    )

    modal = page.locator(
        "#TB_ajaxContent"
    )

    print("高松市選択")

    checkbox = modal.locator(
        'input[value="高松市"]'
    )

    print(
        "checkbox count =",
        checkbox.count()
    )

    checkbox.first.check()

    page.wait_for_timeout(1000)

    save_html(
        page,
        "04_takamatsu_checked.html"
    )

    print("検索実行")

    search_button = modal.locator(
        "a.articleSearchButton"
    )

    print(
        "search button count =",
        search_button.count()
    )

    search_button.first.click()

    page.wait_for_load_state(
        "networkidle"
    )

    save_html(
        page,
        "05_result.html"
    )

    print(
        "result url =",
        page.url
    )

    print(
        "result page loaded"
    )


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        run_search(page)

        browser.close()


if __name__ == "__main__":
    main()