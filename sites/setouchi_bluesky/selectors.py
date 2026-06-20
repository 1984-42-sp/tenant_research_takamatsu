BASE_URL = "https://www.setouchibluesky.jp"

LIST_URL = "https://www.setouchibluesky.jp/kasi-tenpo/kagawa/result/takamatsu-city.html"

SITE_NAME = "setouchi_bluesky"
SITE_LABEL = "瀬戸内ブルースカイ"

EXPECTED_LIST_COUNT = 5
EXPECTED_PAGE_COUNT = 1

DETAIL_URL_KEYWORD = "/kasi-tenpo/detail-"

HTML_LIST_FILENAME = "list_page_1.html"

OUTPUT_LIST_CSV = "setouchi_bluesky_list.csv"
OUTPUT_DETAIL_CSV = "setouchi_bluesky_detail.csv"
OUTPUT_MERGED_CSV = "setouchi_bluesky.csv"
OUTPUT_GEOCODED_CSV = "setouchi_bluesky_geocoded.csv"
OUTPUT_GEOCODE_FAILED_CSV = "setouchi_bluesky_geocode_failed.csv"
OUTPUT_MAP_HTML = "setouchi_bluesky_map.html"

LIST_SELECTORS = {
    "detail_link": f'a[href*="{DETAIL_URL_KEYWORD}"]',
}

DETAIL_SELECTORS = {}

EXCLUDE_KEYWORDS = [
    "お気に入り",
    "お問い合わせ",
    "一括でお問い合わせ",
    "情報の見方",
    "最初へ",
    "前へ",
    "次へ",
    "最後へ",
]