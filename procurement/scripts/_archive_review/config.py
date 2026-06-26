from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"

FRUIT_DIR = DATA_DIR / "fruit"
COFFEE_DIR = DATA_DIR / "coffee"
CONSUMABLE_DIR = DATA_DIR / "consumables"

FINAL_DIR = OUTPUT_DIR / "dashboard"