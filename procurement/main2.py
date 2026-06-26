from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent


STEPS = [
    ("CSV検証", "scripts/validate_csvs.py"),
    ("マスターCSV生成", "scripts/generate_masters.py"),
    ("仕入先位置情報生成", "scripts/prepare_supplier_locations.py"),
    ("地図対象CSV生成", "scripts/prepare_map_targets.py"),
    ("座標補正", "scripts/patch_supplier_coordinates.py"),
    ("仕入先DBダッシュボード生成", "scripts/generate_dashboard.py"),
    ("原価シミュレーターダッシュボード生成", "scripts/generate_cost_simulator_dashboard.py"),
    ("仕入先マップ生成", "scripts/generate_supplier_map.py"),
    ("docs反映", "scripts/update_docs.py"),
]


def run_step(label: str, script: str) -> None:
    path = BASE_DIR / script

    if not path.exists():
        print(f"[SKIP] {label}: {path} が見つかりません")
        return

    print(f"\n=== {label} ===")
    print(f"[RUN] python {script}")

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=BASE_DIR,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"{label} で失敗しました: {script}")


def main() -> None:
    print("=== Procurement Suite main2 ===")
    print(f"[BASE] {BASE_DIR}")

    for label, script in STEPS:
        run_step(label, script)

    print("\n=== 完了 ===")
    print("[OUTPUT] output/dashboard/procurement_dashboard.html")
    print("[OUTPUT] output/dashboard/cost_simulator_dashboard.html")
    print("[OUTPUT] output/dashboard/procurement_supplier_map.html")
    print("[DOCS] docs/")


if __name__ == "__main__":
    main()