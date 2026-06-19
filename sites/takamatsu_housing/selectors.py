# 高松ハウジングサービス用セレクタ

BASE_URL = "https://www.takamatsuhousing.jp"

SOURCE_SITE = "takamatsu_housing"

LIST_PAGE_URL = (
    "https://www.takamatsuhousing.jp/"
    "kasi-tenpo/kagawa/result/takamatsu-city.html"
)

LIST_PAGE_URL_WITH_PAGE = (
    "https://www.takamatsuhousing.jp/"
    "kasi-tenpo/kagawa/result/takamatsu-city.html?page={page}"
)

LIST_OBJECT = "div.article-object.kasi-tenpo"

DETAIL_LINK = 'a[href*="/kasi-tenpo/detail-"]'

DETAIL_ROW = "tr"

DETAIL_CELL = ["th", "td"]

IGNORE_DETAIL_KEYS = {
    "",
    "200万円以下の金額",
    "200万円を超え400万円以下の金額",
    "400万円を超える金額",
}

ADDRESS_COLUMN = "所在地"

RESTAURANT_STATUS_COLUMN = "飲食店可否"

RESTAURANT_NG_KEYWORD = "飲食店不可"

RESTAURANT_OK_KEYWORDS = [
    "飲食店可",
    "軽飲食",
    "重飲食",
]