from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ShortcutMetadata:
    """Parsed metadata needed to download and replace a Steam shortcut icon."""

    shortcut_path: Path
    steam_id: str
    icon_path: Path

    @property
    def icon_name(self) -> str:
        return self.icon_path.name


@dataclass(frozen=True, slots=True)
class ShortcutDiscoveryResult:
    """Shortcut files discovered from the local scan scope."""

    shortcuts: tuple[Path, ...]
    local_shortcut_count: int
    public_shortcut_count: int
