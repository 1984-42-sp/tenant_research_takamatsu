from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "data" / "html" / "google_maps"
OUT_PATH = OUT_DIR / "search_result.html"

GOOGLE_MAPS_URL = "https://www.google.com/maps"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(
            viewport={"width": 1400, "height": 900},
            locale="ja-JP",
        )

        page.goto(GOOGLE_MAPS_URL, wait_until="domcontentloaded")

        print("\n[手動操作]")
        print("1. Google Mapsで「高松市 カフェ」を検索してください")
        print("2. 検索結果一覧が左側に表示されるまで待ってください")
        print("3. 必要なら少しスクロールして店舗一覧を増やしてください")
        print("4. 準備できたら、このPowerShellで Enter を押してください\n")

        input("HTMLを保存するには Enter > ")

        page.wait_for_timeout(2000)
        html = page.content()
        OUT_PATH.write_text(html, encoding="utf-8")

        print(f"[SAVE] {OUT_PATH}")
        print("[DONE] Google Maps検索結果HTMLを保存しました")

        input("ブラウザを閉じるには Enter > ")
        browser.close()


if __name__ == "__main__":
    main()