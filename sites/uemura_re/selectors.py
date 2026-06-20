SITE_NAME = "uemura_re"
SITE_LABEL = "植村不動産"
BASE_URL = "https://www.uemura-re.jp"

LIST_URLS = [
    {
        "category": "貸店舗",
        "url": "https://www.uemura-re.jp/kasi-tenpo/kagawa/result/takamatsu-city.html",
    }
]

EXTRA_DETAIL_URLS = [
    {
        "category": "貸ビル・貸倉庫・その他",
        "url": "https://www.uemura-re.jp/kasi-other/detail-682728ded63cad74d6bc85b5/",
    }
]

EXPECTED_LIST_COUNT = 4
EXPECTED_EXTRA_DETAIL_COUNT = 1
EXPECTED_TOTAL_COUNT = 5

EXCLUDE_KEYWORDS = [
    "成約済",
    "募集終了",
    "居住用",
]