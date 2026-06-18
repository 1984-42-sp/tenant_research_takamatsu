from bs4 import BeautifulSoup
from pathlib import Path


HTML_FILE = Path(
    "data/html/tenant_kagawa_result_page1.html"
)


def main():

    html = HTML_FILE.read_text(
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    hidden_inputs = soup.select(
        'input[id^="ID_ARTICLE_URL_"]'
    )

    print(
        f"hidden件数: {len(hidden_inputs)}"
    )

    for item in hidden_inputs[:20]:

        print(
            item.get("id"),
            item.get("value")
        )


if __name__ == "__main__":
    main()