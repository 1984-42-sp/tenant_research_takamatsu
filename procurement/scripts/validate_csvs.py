from pathlib import Path
import csv
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "output" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    DATA_DIR / "fruit" / "fruit_suppliers.csv",
    DATA_DIR / "coffee" / "coffee_suppliers.csv",
    DATA_DIR / "consumables" / "consumables_suppliers.csv",
    DATA_DIR / "materials" / "materials_suppliers.csv",
    DATA_DIR / "ice" / "ice_suppliers.csv",
    DATA_DIR / "prices" / "price_observations.csv",
    DATA_DIR / "prices" / "fruit_price_observations.csv",
]

def inspect_csv(path: Path):
    result = {
        "file": str(path.relative_to(BASE_DIR)),
        "exists": path.exists(),
        "status": "",
        "header_columns": "",
        "rows": "",
        "bad_lines": "",
        "error": "",
    }

    if not path.exists():
        result["status"] = "missing"
        return result

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            result["status"] = "empty"
            return result

        header_len = len(rows[0])
        bad = []

        for i, row in enumerate(rows[1:], start=2):
            if len(row) != header_len:
                bad.append(f"line {i}: expected {header_len}, saw {len(row)}")

        result["header_columns"] = header_len
        result["rows"] = len(rows) - 1
        result["bad_lines"] = " / ".join(bad[:20])
        result["status"] = "ok" if not bad else "column_mismatch"

        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result

def main():
    results = [inspect_csv(p) for p in TARGETS]
    df = pd.DataFrame(results)

    out_csv = REPORT_DIR / "csv_validation_report.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print(df.to_string(index=False))
    print(f"\n[SAVE] {out_csv}")

if __name__ == "__main__":
    main()