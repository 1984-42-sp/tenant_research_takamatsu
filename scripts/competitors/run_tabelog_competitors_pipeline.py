from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parents[2]

STEPS = [
    ("食べログraw CSV整形", "fetch_tabelog_competitors.py"),
    ("競合データ正規化", "normalize_competitors.py"),
    ("競合住所ジオコーディング", "geocode_competitors.py"),
    ("競合単体マップ生成", "generate_competitors_map.py"),
]


def run_step(label, script_name):
    script_path = BASE_DIR / "scripts" / "competitors" / script_name

    print("")
    print("=" * 60)
    print(f"[START] {label}")
    print(f"[SCRIPT] {script_path}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"[FAILED] {label}: {script_name}")

    print(f"[DONE] {label}")


def main():
    print("[PIPELINE] 食べログ競合データ処理を開始します")

    raw_path = BASE_DIR / "data" / "competitors" / "raw" / "tabelog_cafe_competitors.csv"

    if not raw_path.exists():
        raise FileNotFoundError(
            f"食べログraw CSVがありません: {raw_path}"
        )

    for label, script_name in STEPS:
        run_step(label, script_name)

    print("")
    print("[COMPLETE] 食べログ競合データ処理が完了しました")
    print("[OUTPUT] data\\competitors\\competitors_seed.csv")
    print("[OUTPUT] data\\competitors\\competitors_normalized.csv")
    print("[OUTPUT] data\\competitors\\competitors_geocoded.csv")
    print("[OUTPUT] output\\competitors\\competitors_map.html")


if __name__ == "__main__":
    main()