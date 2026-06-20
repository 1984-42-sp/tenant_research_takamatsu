from pathlib import Path
import time

from playwright.sync_api import sync_playwright

OUT_DIR = Path("data/html/mcrea")


def save_content(page, path: Path, retry: int = 5):
    for attempt in range(1, retry + 1):
        try:
            time.sleep(3)
            html = page.content()
            path.write_text(html, encoding="utf-8")
            print(f"[saved] {path}")
            print(f"[url] {page.url}")
            print(f"[title] {page.title()}")
            return
        except Exception as e:
            print(f"[retry content] {attempt}/{retry}: {repr(e)}")
            time.sleep(5)

    raise RuntimeError(f"HTML保存に失敗しました: {path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(60000)

        page.goto("https://www.mcrea.jp/", wait_until="domcontentloaded", timeout=60000)

        print("ブラウザで以下を手動操作してください:")
        print("1. 貸店舗（テナント）")
        print("2. 高松市")
        print("3. 飲食店可")
        print("4. この条件で検索する")
        print("5. 42件表示の1ページ目まで進む")
        print("6. ページ読み込みが止まってから Enter")
        input("完了したら Enter を押してください...")

        save_content(page, OUT_DIR / "list_page_1.html")

        print("[click] page 2")
        page.click('a[href="/kasi-tenpo/kagawa/result/takamatsu-city.html?page=2"]')
        time.sleep(8)

        save_content(page, OUT_DIR / "list_page_2.html")

        browser.close()


if __name__ == "__main__":
    main()