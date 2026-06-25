from pathlib import Path
import shutil
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
def read_csv_count(path):
    if not path.exists():
        return 0
    return len(pd.read_csv(path))


def build_index_html(template_text):
    properties_path = BASE_DIR / "output" / "archive_csv" / "all_properties.csv"
    dashboard_path = BASE_DIR / "output" / "archive_csv" / "cafe_business_dashboard.csv"
    competitors_path = BASE_DIR / "data" / "competitors" / "competitors_master.csv"

    property_count = read_csv_count(properties_path)
    geocoded_count = read_csv_count(dashboard_path)

    if competitors_path.exists():
        competitors = pd.read_csv(competitors_path)
        competitor_count = len(competitors)
        source_counts = competitors["source"].fillna("").value_counts()
        tabelog_count = int(source_counts.get("tabelog", 0))
        hotpepper_count = int(source_counts.get("hotpepper", 0))
        google_maps_count = int(source_counts.get("google_maps", 0))
    else:
        competitor_count = 0
        tabelog_count = 0
        hotpepper_count = 0
        google_maps_count = 0

    return (
        template_text
        .replace("{{PROPERTY_COUNT}}", str(property_count))
        .replace("{{GEOCODED_PROPERTY_COUNT}}", str(geocoded_count))
        .replace("{{COMPETITOR_COUNT}}", str(competitor_count))
        .replace("{{TABELOG_COUNT}}", str(tabelog_count))
        .replace("{{HOTPEPPER_COUNT}}", str(hotpepper_count))
        .replace("{{GOOGLE_MAPS_COUNT}}", str(google_maps_count))
    )

FINAL_HTML_DIR = BASE_DIR / "output" / "final_html"
COMPETITORS_DIR = BASE_DIR / "output" / "competitors"
REPORTS_DIR = BASE_DIR / "output" / "reports"
TARGET_DIR = BASE_DIR / "docs"

# docs上では従来通り all_properties_map.html として公開する
PUBLIC_FILE_MAP = {
    "all_properties_map.html": COMPETITORS_DIR / "integrated_property_map.html",
    "business_plan_dashboard.html": FINAL_HTML_DIR / "business_plan_dashboard.html",
    "cafe_business_dashboard.html": FINAL_HTML_DIR / "cafe_business_dashboard.html",
    "simulation_index.html": FINAL_HTML_DIR / "simulation_index.html",
    "cafe_business_analysis_report.html": REPORTS_DIR / "cafe_business_analysis_report.html",
}

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


def copy_file_as(src: Path, dst_name: str):
    dst = TARGET_DIR / dst_name

    if not src.exists():
        print(f"[SKIP] not found: {src}")
        return

    shutil.copy2(src, dst)
    print(f"[FILE] {dst_name} <- {src}")


def copy_dir(dirname: str):
    src = FINAL_HTML_DIR / dirname
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

    text = TOP_PAGE.read_text(encoding="utf-8")
    text = build_index_html(text)

    (TARGET_DIR / "index.html").write_text(text, encoding="utf-8")
    print("[FILE] index.html")


def main():
    clean_target_dir()

    copy_top_page()

    for dst_name, src_path in PUBLIC_FILE_MAP.items():
        copy_file_as(src_path, dst_name)

    for dirname in PUBLIC_DIRS:
        copy_dir(dirname)

    print()
    print("[DONE] docs updated")
    print("[MAP ] docs/all_properties_map.html is integrated_property_map.html")


if __name__ == "__main__":
    main()