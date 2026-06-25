from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.chart_tool import generate_all_charts  # noqa: E402


def main() -> None:
    charts = generate_all_charts()
    for chart in charts:
        file_path = Path(chart["file_path"])
        print(f"Chart: {chart['chart_name']}")
        print(f"Path: {file_path}")
        print(f"Description: {chart['description']}")
        print(f"Exists: {file_path.exists()}")
        print()


if __name__ == "__main__":
    main()
