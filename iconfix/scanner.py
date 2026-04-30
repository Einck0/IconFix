from __future__ import annotations

from pathlib import Path

from .constants import PUBLIC_DESKTOP_PATH
from .models import ShortcutDiscoveryResult


def _find_shortcut_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*.url") if path.is_file())


def _deduplicate(paths: list[Path]) -> tuple[Path, ...]:
    deduplicated: list[Path] = []
    seen: set[str] = set()

    for path in paths:
        normalized = str(path.resolve()).casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(path)

    return tuple(deduplicated)


def discover_shortcuts(base_path: Path) -> ShortcutDiscoveryResult:
    """Collect URL shortcut files from the target folder and public desktop."""
    local_shortcuts = _find_shortcut_files(base_path)
    public_shortcuts = _find_shortcut_files(PUBLIC_DESKTOP_PATH)
    shortcuts = _deduplicate([*local_shortcuts, *public_shortcuts])

    return ShortcutDiscoveryResult(
        shortcuts=shortcuts,
        local_shortcut_count=len(local_shortcuts),
        public_shortcut_count=len(public_shortcuts),
    )
