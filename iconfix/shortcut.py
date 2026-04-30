from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import ShortcutMetadata

STEAM_URL_PATTERN = re.compile(r"^steam://rungameid/(?P<steam_id>\d+)$", re.IGNORECASE)


class ShortcutParseError(ValueError):
    """Raised when a shortcut cannot be parsed as a Steam game shortcut."""


def _parse_key_value_lines(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("[") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_shortcut_text(shortcut_path: Path, content: str) -> ShortcutMetadata:
    """Parse the Steam shortcut metadata from a .url file body."""
    values = _parse_key_value_lines(content)
    shortcut_url = values.get("URL")
    icon_file = values.get("IconFile")

    if not shortcut_url:
        raise ShortcutParseError("缺少 URL 字段。")
    if not icon_file:
        raise ShortcutParseError("缺少 IconFile 字段。")

    steam_id_match = STEAM_URL_PATTERN.match(shortcut_url)
    if not steam_id_match:
        raise ShortcutParseError("不是 Steam 游戏快捷方式。")

    return ShortcutMetadata(
        shortcut_path=shortcut_path,
        steam_id=steam_id_match.group("steam_id"),
        icon_path=Path(icon_file),
    )


def load_shortcut_metadata(shortcut_path: Path) -> ShortcutMetadata | None:
    """Read and parse a Steam shortcut file, logging a warning on invalid input."""
    try:
        content = shortcut_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        logging.error("读取快捷方式失败 %s: %s", shortcut_path, exc)
        return None

    try:
        return parse_shortcut_text(shortcut_path, content)
    except ShortcutParseError as exc:
        logging.warning("跳过 %s: %s", shortcut_path, exc)
        return None
