from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = BASE_DIR / "output" / "final_html"
TARGET_DIR = BASE_DIR / "netlify_public"

PUBLIC_FILES = [
    "all_properties_map.html",
    "business_plan_dashboard.html",
    "cafe_business_dashboard.html",
    "simulation_index.html",
]

PUBLIC_DIRS = [
    "property_business_simulations",
]

TOP_PAGE = BASE_DIR / "templates" / "netlify_index.html"


def clean_target_dir():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for item in TARGET_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_file(filename: str):
    src = SOURCE_DIR / filename
    dst = TARGET_DIR / filename

    if not src.exists():
        print(f"[SKIP] not found: {src}")
        return

    shutil.copy2(src, dst)
    print(f"[FILE] {filename}")


def copy_dir(dirname: str):
    src = SOURCE_DIR / dirname
    dst = TARGET_DIR / dirname

    if not src.exists():
        print(f"[SKIP] not found: {src}")
        return

    shutil.copytree(src, dst)
    print(f"[DIR ] {dirname}")


def copy_top_page():
    if not TOP_PAGE.exists():
        print(f"[SKIP] not found: {TOP_PAGE}")
        return

    shutil.copy2(TOP_PAGE, TARGET_DIR / "index.html")
    print("[FILE] index.html")


def main():
    clean_target_dir()

    copy_top_page()

    for filename in PUBLIC_FILES:
        copy_file(filename)

    for dirname in PUBLIC_DIRS:
        copy_dir(dirname)

    print()
    print("[DONE] netlify_public updated")


if __name__ == "__main__":
    main()

    