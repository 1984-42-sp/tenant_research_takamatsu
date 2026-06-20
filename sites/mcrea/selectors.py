SITE_NAME = "mcrea"
SITE_LABEL = "エムクレア"
BASE_URL = "https://www.mcrea.jp"

LIST_URLS = [
    {
        "page": 1,
        "url": "https://www.mcrea.jp/kasi-tenpo/kagawa/result/takamatsu-city.html",
    },
    {
        "page": 2,
        "url": "https://www.mcrea.jp/kasi-tenpo/kagawa/result/takamatsu-city.html?page=2",
    },
]

EXPECTED_LIST_COUNT = 42
EXPECTED_TOTAL_COUNT = 42

EXCLUDE_KEYWORDS = [
    "成約済",
    "募集終了",
    "居住用",
]