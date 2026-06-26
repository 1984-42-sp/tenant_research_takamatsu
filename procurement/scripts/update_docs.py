from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[1]

DOCS_DIR = BASE / "docs"
DASHBOARD_DIR = BASE / "output" / "dashboard"

# docs に公開する成果物を明示する。
# output/dashboard 配下を丸ごとコピーすると、検証用・旧版HTMLまで混入する可能性があるため避ける。
PUBLISH_TARGETS = [
    {
        "label": "仕入先DBダッシュボード",
        "source": DASHBOARD_DIR / "procurement_dashboard.html",
        "destination": DOCS_DIR / "procurement_dashboard.html",
        "required": True,
    },
    {
        "label": "原価シミュレーターダッシュボード",
        "source": DASHBOARD_DIR / "cost_simulator_dashboard.html",
        "destination": DOCS_DIR / "cost_simulator_dashboard.html",
        "required": True,
    },
    {
        "label": "仕入先マップ",
        "source": DASHBOARD_DIR / "procurement_supplier_map.html",
        "destination": DOCS_DIR / "procurement_supplier_map.html",
        "required": True,
    },
]


def copy_file(label: str, source: Path, destination: Path, required: bool = True) -> bool:
    if not source.exists():
        level = "ERROR" if required else "WARN"
        print(f"[{level}] {label}: コピー元が見つかりません: {source}")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[COPY] {label}: {source.relative_to(BASE)} -> {destination.relative_to(BASE)}")
    return True


def main() -> None:
    print("=== update docs ===")
    print(f"[BASE] {BASE}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    ok_count = 0
    missing_required = []

    for item in PUBLISH_TARGETS:
        ok = copy_file(
            label=item["label"],
            source=item["source"],
            destination=item["destination"],
            required=item.get("required", True),
        )
        if ok:
            ok_count += 1
        elif item.get("required", True):
            missing_required.append(item["label"])

    print(f"[DONE] copied: {ok_count}/{len(PUBLISH_TARGETS)}")

    if missing_required:
        names = " / ".join(missing_required)
        raise RuntimeError(f"必須成果物の docs 反映に失敗しました: {names}")

    print("docs updated.")


if __name__ == "__main__":
    main()
