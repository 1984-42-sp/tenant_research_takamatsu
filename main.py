from pathlib import Path
import os
import shutil
import subprocess
import sys
import time


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# 実行タスク定義
# ============================================================

PROPERTY_PIPELINE_TASKS = [
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
    "scripts/generate_enhanced_property_map.py",
]

COMPETITOR_INTEGRATION_TASKS = [
    "scripts/competitors/merge_property_competitors.py",
    "scripts/competitors/merge_dashboard_competitors.py",
    "scripts/competitors/generate_integrated_enhanced_property_map.py",
    "scripts/reports/generate_cafe_business_analysis_report.py",
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


# ============================================================
# 共通ユーティリティ
# ============================================================

def ask_yes_no(message: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"

    while True:
        answer = input(f"{message} {suffix}: ").strip().lower()

        if not answer:
            return default

        if answer in {"y", "yes"}:
            return True

        if answer in {"n", "no"}:
            return False

        print("y または n で入力してください。")


def ask_choice(message: str, choices: dict[str, str], default: str) -> str:
    print()
    print(message)

    for key, label in choices.items():
        print(f"  {key}: {label}")

    while True:
        answer = input(f"選択 [{default}]: ").strip().lower() or default

        if answer in choices:
            return answer

        print("表示されている選択肢から入力してください。")


def run_script(script_path: str, *, env: dict[str, str] | None = None) -> None:
    full_path = BASE_DIR / script_path

    print()
    print("=" * 80)
    print(f"[RUN] {script_path}")
    print("=" * 80)

    if not full_path.exists():
        raise FileNotFoundError(f"スクリプトが見つかりません: {full_path}")

    run_env = os.environ.copy()

    if env:
        run_env.update(env)

    result = subprocess.run(
        [sys.executable, str(full_path)],
        cwd=BASE_DIR,
        env=run_env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FAILED: {script_path}")

    print(f"[OK] {script_path}")


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"[SKIP] missing: {src}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[COPY] {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}")


def wait_enter(message: str = "準備ができたら Enter を押してください。") -> None:
    input(f"\n{message}")


# ============================================================
# サイト調査フェーズ
# ============================================================

def run_tabelog_phase() -> None:
    if not ask_yes_no("食べログの競合調査を実行しますか？", default=False):
        print("[SKIP] 食べログ")
        return

    run_script("scripts/competitors/run_tabelog_competitors_pipeline.py")


def run_hotpepper_phase() -> None:
    if not ask_yes_no("ホットペッパーグルメの競合調査を実行しますか？", default=False):
        print("[SKIP] ホットペッパーグルメ")
        return

    api_key = os.environ.get("HOTPEPPER_API_KEY", "").strip()

    if not api_key:
        print()
        print("[WARN] HOTPEPPER_API_KEY が環境変数に設定されていません。")
        print("PowerShellで事前設定する場合:")
        print('$env:HOTPEPPER_API_KEY="xxxxxxxx"')

        if not ask_yes_no("この工程をスキップしますか？", default=True):
            api_key = input("HOTPEPPER_API_KEY を入力してください: ").strip()

    if not api_key:
        print("[SKIP] ホットペッパーグルメ")
        return

    run_script(
        "scripts/competitors/fetch_hotpepper_competitors.py",
        env={"HOTPEPPER_API_KEY": api_key},
    )


def run_google_maps_phase() -> None:
    if not ask_yes_no("Googleマップの競合調査を実行しますか？", default=False):
        print("[SKIP] Googleマップ")
        return

    mode = ask_choice(
        "Googleマップ取得モードを選択してください。",
        {
            "b": "B. 一覧取得のみ",
            "a": "A. 一覧取得 + 手動詳細URL取得あり",
        },
        default="b",
    )

    print()
    print("Google Maps操作手順")
    print("1. Google Mapsで「高松市 カフェ」を検索")
    print("2. 一覧を必要件数までスクロール")

    if mode == "b":
        print("3. PowerShellで Enter")
        print("4. 詳細取得フェーズに入ったら q で終了")
        wait_enter("ブラウザ操作を開始できる状態にして Enter を押してください。")

        run_script("sites/google_maps/fetch_search.py")
        run_script("sites/google_maps/extract.py")
        run_script("sites/google_maps/attach_coords.py")
        run_script("scripts/competitors/normalize_competitors.py")
        return

    print("3. PowerShellで Enter")
    print("4. 店舗カードを1件クリック")
    print("5. 詳細パネル表示後、PowerShellで Enter")
    print("6. 次の店舗カードをクリック → Enter を繰り返す")
    print("7. 終了時は q")
    wait_enter("ブラウザ操作を開始できる状態にして Enter を押してください。")

    run_script("sites/google_maps/fetch_search.py")
    run_script("sites/google_maps/extract_details.py")

    print()
    print("必要に応じてCSVを手修正してください:")
    print(r"output\google_maps\google_maps_cafes_from_details.csv")

    if ask_yes_no("手修正が完了し、最終CSVへコピーしますか？", default=True):
        src = BASE_DIR / "output" / "google_maps" / "google_maps_cafes_from_details.csv"
        dst = BASE_DIR / "output" / "google_maps" / "google_maps_geocoded.csv"
        copy_file(src, dst)

    run_script("scripts/competitors/normalize_competitors.py")


def run_site_research_phase() -> None:
    print()
    print("====================================")
    print("サイト調査フェーズ")
    print("====================================")
    print("各サイト調査は必要なものだけ実行できます。")

    run_tabelog_phase()
    run_hotpepper_phase()
    run_google_maps_phase()


# ============================================================
# 物件・競合 統合出力フェーズ
# ============================================================

def organize_property_outputs() -> None:
    output_dir = BASE_DIR / "output"
    all_dir = output_dir / "all_properties"

    final_html_dir = output_dir / "final_html"
    archive_csv_dir = output_dir / "archive_csv"
    debug_dir = archive_csv_dir / "debug"

    final_html_dir.mkdir(parents=True, exist_ok=True)
    archive_csv_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("====================================")
    print("物件成果物整理開始")
    print("====================================")

    for file_name in FINAL_HTML_FILES:
        src = all_dir / file_name
        if not src.exists():
            continue

        dst = final_html_dir / file_name
        shutil.move(src, dst)
        print(f"[HTML] {file_name}")

    sim_index_src = all_dir / "index.html"
    if sim_index_src.exists():
        sim_index_dst = final_html_dir / "simulation_index.html"
        shutil.move(sim_index_src, sim_index_dst)
        print("[HTML] simulation_index.html")

    sim_src = all_dir / "property_business_simulations"
    sim_dst = final_html_dir / "property_business_simulations"

    if sim_src.exists():
        if sim_dst.exists():
            shutil.rmtree(sim_dst)

        shutil.move(sim_src, sim_dst)
        print("[HTML] property_business_simulations")

    for file_name in CSV_FILES:
        src = all_dir / file_name
        if not src.exists():
            continue

        dst = archive_csv_dir / file_name
        shutil.move(src, dst)
        print(f"[CSV] {file_name}")

    for file_name in DEBUG_FILES:
        src = all_dir / file_name
        if not src.exists():
            continue

        dst = debug_dir / file_name
        shutil.move(src, dst)
        print(f"[DEBUG] {file_name}")


def run_property_pipeline_phase() -> None:
    print()
    print("====================================")
    print("物件統合・評価フェーズ")
    print("====================================")

    for task in PROPERTY_PIPELINE_TASKS:
        run_script(task)

    organize_property_outputs()


def run_competitor_integration_phase() -> None:
    print()
    print("====================================")
    print("競合統合・最終出力フェーズ")
    print("====================================")

    for task in COMPETITOR_INTEGRATION_TASKS:
        run_script(task)


# ============================================================
# main
# ============================================================

def main() -> None:
    start = time.time()

    print()
    print("====================================")
    print("高松市 カフェ物件・競合調査 統合パイプライン")
    print("====================================")
    print(f"[BASE] {BASE_DIR}")
    print()
    print("注意:")
    print("この main.py は scripts/update_docs.py を実行しません。")
    print("GitHub Pages公開用 docs 反映は、必ず別工程で実行してください。")

    if ask_yes_no("サイト調査フェーズを実行しますか？", default=False):
        run_site_research_phase()
    else:
        print("[SKIP] サイト調査フェーズ")

    if ask_yes_no("物件統合・評価フェーズを実行しますか？", default=True):
        run_property_pipeline_phase()
    else:
        print("[SKIP] 物件統合・評価フェーズ")

    if ask_yes_no("競合統合・最終出力フェーズを実行しますか？", default=True):
        run_competitor_integration_phase()
    else:
        print("[SKIP] 競合統合・最終出力フェーズ")

    elapsed = time.time() - start

    print()
    print("====================================")
    print("main.py 全処理完了")
    print(f"所要時間: {elapsed:.1f}秒")
    print("====================================")
    print()
    print("次工程の例:")
    print("1. Procurement Suite 側で main2.py を実行")
    print("2. 本プロジェクト側で python scripts/update_docs.py を実行")
    print()
    print("この main.py から update_docs.py は呼び出していません。")


if __name__ == "__main__":
    main()
