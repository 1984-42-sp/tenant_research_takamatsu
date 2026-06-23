from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = BASE_DIR / "output" / "final_html"
TARGET_DIR = BASE_DIR / "netlify_public"


def main():
    TARGET_DIR.mkdir(exist_ok=True)

    for item in SOURCE_DIR.iterdir():

        dst = TARGET_DIR / item.name

        if item.is_dir():

            if dst.exists():
                shutil.rmtree(dst)

            shutil.copytree(item, dst)

            print(f"[DIR ] {item.name}")

        else:

            shutil.copy2(item, dst)

            print(f"[FILE] {item.name}")

    print()
    print("[DONE] netlify_public updated")


if __name__ == "__main__":
    main()

TOP_PAGE = BASE_DIR / "templates" / "netlify_index.html"

if TOP_PAGE.exists():
    shutil.copy2(
        TOP_PAGE,
        TARGET_DIR / "index.html"
    )
    print("[FILE] index.html")