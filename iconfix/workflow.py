from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import ShortcutMetadata
from .scanner import discover_shortcuts
from .shortcut import load_shortcut_metadata
from .steam import IconDownloadError, SteamIconClient


def parse_selection(raw_text: str, max_index: int) -> list[int]:
    """Parse user input like '1 2 3' or '1,2,3' into a validated selection."""
    if not raw_text.strip():
        return []

    tokens = [token for token in re.split(r"[\s,]+", raw_text.strip()) if token]
    try:
        indexes = [int(token) for token in tokens]
    except ValueError as exc:
        raise ValueError("请输入数字编号，多个编号可用空格或逗号分隔。") from exc

    if any(index < 0 for index in indexes):
        raise ValueError("编号不能为负数。")

    if 0 in indexes:
        return list(range(1, max_index + 1))

    invalid_indexes = [index for index in indexes if index > max_index]
    if invalid_indexes:
        raise ValueError(f"存在超出范围的编号: {invalid_indexes}")

    return sorted(set(indexes))


def select_shortcuts(shortcuts: tuple[Path, ...], auto_select_all: bool) -> list[Path]:
    """Prompt the user to select shortcuts, or select everything automatically."""
    if auto_select_all:
        return list(shortcuts)

    print("0: 全部文件")
    for index, shortcut_path in enumerate(shortcuts, start=1):
        print(f"{index}: {shortcut_path}")

    user_input = input("\n请选择要修复的快捷方式编号（空格或逗号分隔）: ").strip()
    selection = parse_selection(user_input, len(shortcuts))
    return [shortcuts[index - 1] for index in selection]


def _write_icon(icon_metadata: ShortcutMetadata, icon_bytes: bytes) -> None:
    icon_metadata.icon_path.parent.mkdir(parents=True, exist_ok=True)
    icon_metadata.icon_path.write_bytes(icon_bytes)


def process_icons(base_path: Path, auto_select_all: bool) -> int:
    """Drive the end-to-end icon repair workflow."""
    logging.info("正在扫描快捷方式目录: %s", base_path)
    discovery = discover_shortcuts(base_path)

    if not discovery.shortcuts:
        logging.info("没有发现任何 .url 快捷方式，程序结束。")
        return 0

    logging.info(
        "共发现 %s 个快捷方式（当前目录 %s 个，公共桌面 %s 个）。",
        len(discovery.shortcuts),
        discovery.local_shortcut_count,
        discovery.public_shortcut_count,
    )

    selected_shortcuts = select_shortcuts(discovery.shortcuts, auto_select_all)
    if not selected_shortcuts:
        logging.info("未选择任何快捷方式，程序结束。")
        return 0

    logging.info("开始修复图标，请稍候...")
    client = SteamIconClient()
    success_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        for shortcut_path in selected_shortcuts:
            metadata = load_shortcut_metadata(shortcut_path)
            if metadata is None:
                skipped_count += 1
                continue

            try:
                icon_bytes = client.download_icon_bytes(metadata)
                _write_icon(metadata, icon_bytes)
            except PermissionError:
                failed_count += 1
                logging.error("写入图标失败，权限不足: %s", metadata.icon_path)
                continue
            except (IconDownloadError, OSError) as exc:
                failed_count += 1
                logging.error("处理失败 %s: %s", shortcut_path, exc)
                continue

            success_count += 1
            logging.info("修复成功: %s", shortcut_path)
    finally:
        client.close()

    logging.info(
        "修复完成：成功 %s 个，失败 %s 个，跳过 %s 个。",
        success_count,
        failed_count,
        skipped_count,
    )
    return 0 if failed_count == 0 else 1
