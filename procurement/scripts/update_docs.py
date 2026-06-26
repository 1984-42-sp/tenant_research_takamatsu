from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[1]

DOCS = BASE / "docs"
OUT = BASE / "output" / "dashboard"

DOCS.mkdir(exist_ok=True)

for f in OUT.glob("*"):
    shutil.copy2(f, DOCS / f.name)

print("docs updated.")