from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import __version__
from .constants import APP_NAME
from .elevation import ElevationResult, ensure_admin, is_running_as_admin
from .logging_utils import configure_logging
from .workflow import process_icons


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="修复 Steam 游戏快捷方式的图标文件。",
    )
    parser.add_argument(
        "-path",
        "--path",
        default=os.getcwd(),
        help="指定要扫描的目录，默认使用当前目录。",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="不进行交互选择，直接处理扫描到的全部快捷方式。",
    )
    parser.add_argument(
        "--no-elevate",
        action="store_true",
        help="跳过自动申请管理员权限。",
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="执行结束后不等待按键，适合脚本化调用。",
    )
    parser.add_argument(
        "--elevated",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def pause_if_needed(should_pause: bool) -> None:
    if not should_pause:
        return
    if not sys.stdin or not sys.stdin.isatty():
        return

    try:
        input("\n按回车键退出...")
    except EOFError:
        return


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    target_path = Path(args.path).expanduser().resolve()
    should_pause = not args.no_pause

    try:
        elevation_state = ensure_admin(
            auto_elevate=not args.no_elevate,
            launched_from_elevated_restart=args.elevated,
        )

        if elevation_state is ElevationResult.RELAUNCHED:
            logging.info("已发起管理员授权请求，授权通过后将在新窗口继续执行。")
            should_pause = False
            return 0
        if elevation_state is ElevationResult.CANCELLED:
            logging.warning("你取消了管理员授权，程序未继续执行。")
            return 1
        if elevation_state is ElevationResult.FAILED:
            logging.error("管理员提权失败，请手动以管理员身份运行后重试。")
            return 1
        if args.no_elevate and not is_running_as_admin():
            logging.warning("当前未以管理员身份运行，部分受保护目录可能无法写入。")

        logging.info("%s v%s 启动。", APP_NAME, __version__)
        return process_icons(target_path, auto_select_all=args.all)
    except KeyboardInterrupt:
        logging.warning("用户中断了本次执行。")
        return 1
    except Exception:
        logging.exception("程序运行时发生未处理异常。")
        return 1
    finally:
        pause_if_needed(should_pause)
