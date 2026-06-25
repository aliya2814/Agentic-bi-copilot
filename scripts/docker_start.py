from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"
REQUIRED_DIRS = [
    ROOT_DIR / "data" / "processed",
    ROOT_DIR / "outputs" / "charts",
    ROOT_DIR / "outputs" / "evals",
]


def ensure_runtime_files() -> None:
    for folder in REQUIRED_DIRS:
        folder.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "create_sample_db.py")],
            cwd=ROOT_DIR,
            check=True,
        )


def main() -> None:
    ensure_runtime_files()
    os.execvp(
        "streamlit",
        [
            "streamlit",
            "run",
            "app/streamlit_app.py",
            "--server.address=0.0.0.0",
            "--server.port=8501",
        ],
    )


if __name__ == "__main__":
    main()
