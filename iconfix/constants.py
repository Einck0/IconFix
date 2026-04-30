from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "IconFix"
ELEVATION_SENTINEL = "--elevated"
DEFAULT_HTTP_TIMEOUT = 10
PUBLIC_DESKTOP_PATH = Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
}
