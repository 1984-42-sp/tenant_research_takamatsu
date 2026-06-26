from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]

README = BASE_DIR / "README.md"

now = datetime.now().strftime("%Y-%m-%d %H:%M")

text = f"""# Procurement Research

更新日時

{now}

## 調査対象

- フルーツ
- コーヒー豆
- 消耗品

## データ

data/

output/

docs/

"""

README.write_text(text, encoding="utf-8")

print("README generated.")