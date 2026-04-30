from __future__ import annotations

import logging


def configure_logging() -> None:
    """Configure a consistent console logger for the app."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
