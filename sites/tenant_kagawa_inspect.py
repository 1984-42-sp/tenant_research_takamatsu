from playwright.sync_api import sync_playwright


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

        print("URL:", page.url)
        print("TITLE:", page.title())

        input("F12で要素を確認したらEnter")

        browser.close()


if __name__ == "__main__":
    main()