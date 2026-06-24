from pathlib import Path
from datetime import datetime
import csv
import re
import time
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[2]

OUT_DIR = BASE_DIR / "data" / "html" / "google_maps"
SEARCH_OUT_PATH = OUT_DIR / "search_result.html"

DETAIL_DIR = OUT_DIR / "details"
MANIFEST_PATH = OUT_DIR / "details_manifest.csv"

GOOGLE_MAPS_URL = "https://www.google.com/maps"

MANIFEST_COLUMNS = ["store_name", "detail_html", "google_maps_url", "saved_at"]


def safe_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]", "_", value.strip())
    value = re.sub(r"\s+", "_", value)
    return value[:80] if value else "unknown"


def format_elapsed(seconds: float) -> str:
    seconds = int(seconds)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}時間{minutes}分{sec}秒"
    if minutes:
        return f"{minutes}分{sec}秒"
    return f"{sec}秒"


def load_saved_store_names() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()

    names = set()
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("store_name", "").strip()
            if name:
                names.add(name)
    return names


def append_manifest(row: dict):
    exists = MANIFEST_PATH.exists()
    with MANIFEST_PATH.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def clean_store_name(name: str) -> str:
    name = name.strip()

    remove_suffixes = [
        " - Google マップ",
        " - Google Maps",
        " - Google 検索",
    ]

    for suffix in remove_suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()

    return name


def get_current_store_name(page) -> str:
    # Google Maps詳細ページでは title が一番安定する
    try:
        title = page.title().strip()
        name = clean_store_name(title)
        if name and name not in {"Google マップ", "Google Maps", "結果"}:
            return name
    except Exception:
        pass

    # titleで取れない場合だけh1を見る
    selectors = [
        "h1.DUwDvf",
        "h1",
        "div[role='main'] h1",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.count() > 0:
                text = clean_store_name(loc.inner_text(timeout=3000))
                if text and text not in {"Google マップ", "Google Maps", "結果"}:
                    return text
        except Exception:
            pass

    return ""


def save_search_result(page):
    page.wait_for_timeout(1500)
    SEARCH_OUT_PATH.write_text(page.content(), encoding="utf-8")
    print(f"[SAVE] 一覧HTML: {SEARCH_OUT_PATH}")


def save_detail_page(page, store_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_filename(store_name)}.html"
    out_path = DETAIL_DIR / filename

    page.wait_for_timeout(1500)
    out_path.write_text(page.content(), encoding="utf-8")
    return out_path


def main():
    start_time = time.time()
    start_dt = datetime.now()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)

    saved_store_names = load_saved_store_names()

    saved_count = 0
    skip_count = 0
    checked_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(
            viewport={"width": 1400, "height": 900},
            locale="ja-JP",
        )

        page.goto(GOOGLE_MAPS_URL, wait_until="domcontentloaded")

        print("\n[手動操作 1: 一覧取得]")
        print("1. Google Mapsで検索してください")
        print("   例: 高松市 カフェ")
        print("2. 左側に店舗一覧が表示されたら、必要件数までスクロールしてください")
        print("3. 準備できたら、このPowerShellで Enter を押してください\n")

        input("一覧HTMLを保存するには Enter > ")
        save_search_result(page)

        print("\n[手動操作 2: 店舗詳細取得]")
        print("1. 店舗カードを1件クリックしてください")
        print("2. 左側詳細パネルの店名が表示されるまで待ってください")
        print("3. このPowerShellで Enter を押してください")
        print("4. 終了する場合は q を入力して Enter\n")

        while True:
            command = input("店舗詳細を保存: Enter / 終了: q > ").strip().lower()

            if command == "q":
                break

            checked_count += 1
            page.wait_for_timeout(2000)

            store_name = get_current_store_name(page)

            if not store_name:
                print("[WARN] 店舗名を取得できませんでした。詳細パネルを開いた状態で再度 Enter。")
                continue

            print(f"[DETECT] 現在の店舗: {store_name}")

            if store_name in saved_store_names:
                skip_count += 1
                print(f"[SKIP] 既に取得済み: {store_name}")
                print("       次の店舗カードをクリックしてください。")
                continue

            detail_path = save_detail_page(page, store_name)
            google_maps_url = page.url
            saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            append_manifest(
                {
                    "store_name": store_name,
                    "detail_html": str(detail_path.relative_to(BASE_DIR)),
                    "google_maps_url": google_maps_url,
                    "saved_at": saved_at,
                }
            )

            saved_store_names.add(store_name)
            saved_count += 1

            elapsed = time.time() - start_time
            avg = elapsed / max(checked_count, 1)

            print(f"[SAVE] {store_name}")
            print(f"       {detail_path}")
            print(f"       保存 {saved_count}件 / スキップ {skip_count}件 / 確認 {checked_count}件")
            print(f"       平均 {avg:.1f}秒/件")

        end_dt = datetime.now()
        elapsed = time.time() - start_time

        print("\n========================================")
        print("Google Maps Detail Collector")
        print("========================================")
        print(f"[SAVE] {saved_count}件")
        print(f"[SKIP] {skip_count}件")
        print(f"[CHECKED] {checked_count}件")
        print(f"開始時刻 : {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"終了時刻 : {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"経過時間 : {format_elapsed(elapsed)}")
        print(f"一覧HTML : {SEARCH_OUT_PATH}")
        print(f"詳細HTML : {DETAIL_DIR}")
        print(f"管理CSV  : {MANIFEST_PATH}")
        print("========================================")

        input("ブラウザを閉じるには Enter > ")
        browser.close()


if __name__ == "__main__":
    main()