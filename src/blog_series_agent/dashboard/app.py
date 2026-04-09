"""Dashboard launcher and Streamlit entrypoint."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_dashboard() -> None:
    """Launch the Streamlit dashboard."""

    dashboard_script = Path(__file__).with_name("ui.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_script)], check=True)

