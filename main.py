from pathlib import Path
import subprocess
import sys
import time
import shutil


BASE_DIR = Path(__file__).resolve().parent


TASKS = [
    "scripts/merge_all_properties.py",

    "scripts/evaluate_cafe_properties_v2.py",

    "scripts/generate_business_plan_dashboard_csv.py",

    # ブランド順位・星評価を
    # cafe_property_evaluation.csv / cafe_business_dashboard.csv
    # に反映するため再実行
    "scripts/evaluate_cafe_properties_v2.py",

    "scripts/generate_business_plan_dashboard_html.py",

    "scripts/generate_property_business_simulations.py",

    "scripts/generate_cafe_business_dashboard.py",
]


FINAL_HTML_FILES = [
    "all_properties_map.html",
    "cafe_property_evaluation.html",
    "cafe_business_dashboard.html",
    "business_plan_dashboard.html",
]


CSV_FILES = [
    "all_properties.csv",
    "all_properties_geocoded.csv",
    "all_properties_geocode_failed.csv",
    "cafe_property_evaluation.csv",
    "cafe_business_dashboard.csv",
    "business_plan_dashboard.csv",
    "property_business_simulations_index.csv",
]


DEBUG_FILES = [
    "all_properties_deduplicated.csv",
    "all_properties_duplicate_candidates.csv",
]


def organize_outputs():

    output_dir = BASE_DIR / "output"
    all_dir = output_dir / "all_properties"

    final_html_dir = output_dir / "final_html"
    archive_csv_dir = output_dir / "archive_csv"
    debug_dir = archive_csv_dir / "debug"

    final_html_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    archive_csv_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    debug_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("====================================")
    print("成果物整理開始")
    print("====================================")

    #
    # HTML成果物
    #

    for file_name in FINAL_HTML_FILES:

        src = all_dir / file_name

        if not src.exists():
            continue

        dst = final_html_dir / file_name

        shutil.move(src, dst)

        print(f"[HTML] {file_name}")

    #
    # simulation index
    #

    sim_index_src = all_dir / "index.html"

    if sim_index_src.exists():

        sim_index_dst = (
            final_html_dir
            / "simulation_index.html"
        )

        shutil.move(
            sim_index_src,
            sim_index_dst
        )

        print("[HTML] simulation_index.html")

    #
    # simulation pages
    #

    sim_src = (
        all_dir
        / "property_business_simulations"
    )

    sim_dst = (
        final_html_dir
        / "property_business_simulations"
    )

    if sim_src.exists():

        if sim_dst.exists():
            shutil.rmtree(sim_dst)

        shutil.move(
            sim_src,
            sim_dst
        )

        print("[HTML] property_business_simulations")

    #
    # CSV
    #

    for file_name in CSV_FILES:

        src = all_dir / file_name

        if not src.exists():
            continue

        dst = archive_csv_dir / file_name

        shutil.move(
            src,
            dst
        )

        print(f"[CSV] {file_name}")

    #
    # debug
    #

    for file_name in DEBUG_FILES:

        src = all_dir / file_name

        if not src.exists():
            continue

        dst = debug_dir / file_name

        shutil.move(
            src,
            dst
        )

        print(f"[DEBUG] {file_name}")


def run_task(script_path):

    full_path = BASE_DIR / script_path

    print()
    print("=" * 80)
    print(f"[RUN] {script_path}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, str(full_path)]
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FAILED: {script_path}"
        )

    print(f"[OK] {script_path}")


def main():

    start = time.time()

    print()
    print("====================================")
    print("高松市 カフェ事業性評価パイプライン")
    print("====================================")

    for task in TASKS:
        run_task(task)

    organize_outputs()

    elapsed = time.time() - start

    print()
    print("====================================")
    print("全処理完了")
    print(f"所要時間: {elapsed:.1f}秒")
    print("====================================")


if __name__ == "__main__":
    main()