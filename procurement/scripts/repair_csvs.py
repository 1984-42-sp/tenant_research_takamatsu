from pathlib import Path
import csv
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "output" / "backup_csv"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    DATA_DIR / "coffee" / "coffee_suppliers.csv",
    DATA_DIR / "consumables" / "consumables_suppliers.csv",
    DATA_DIR / "prices" / "price_observations.csv",
    DATA_DIR / "prices" / "fruit_price_observations.csv",
]

def repair(path: Path):
    if not path.exists():
        print(f"[SKIP] missing: {path}")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"{path.stem}_{ts}.csv"
    backup.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        print(f"[SKIP] empty: {path}")
        return

    header = rows[0]
    n = len(header)

    fixed = [header]
    changed = 0

    for row in rows[1:]:
        original_len = len(row)

        if original_len < n:
            row = row + [""] * (n - original_len)
            changed += 1

        elif original_len > n:
            # 末尾列を notes とみなし、はみ出し分を最後の列へ結合
            keep = row[: n - 1]
            tail = row[n - 1 :]
            row = keep + [" / ".join([x for x in tail if x != ""])]
            changed += 1

        fixed.append(row)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(fixed)

    print(f"[REPAIR] {path.relative_to(BASE_DIR)} rows={len(fixed)-1} changed={changed} backup={backup.relative_to(BASE_DIR)}")

def main():
    for p in TARGETS:
        repair(p)

if __name__ == "__main__":
    main()