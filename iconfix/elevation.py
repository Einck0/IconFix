from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
from enum import Enum, auto
from typing import Sequence

from .constants import ELEVATION_SENTINEL


class ElevationResult(Enum):
    READY = auto()
    RELAUNCHED = auto()
    CANCELLED = auto()
    FAILED = auto()


def is_running_as_admin() -> bool:
    """Return True when the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception as exc:  # pragma: no cover - Windows API failure is environment-specific.
        logging.error("检查管理员权限时发生异常: %s", exc)
        return False


def build_elevated_invocation(
    argv: Sequence[str] | None = None,
    *,
    frozen: bool | None = None,
    executable: str | None = None,
    script_path: str | None = None,
) -> tuple[str, str]:
    """Build the executable and argument string used for ShellExecuteW."""
    current_argv = list(argv or sys.argv)
    current_executable = executable or sys.executable
    current_script = script_path or os.path.abspath(current_argv[0])
    is_frozen_app = getattr(sys, "frozen", False) if frozen is None else frozen

    forwarded_args = [
        arg for arg in current_argv[1:] if arg.strip().lower() != ELEVATION_SENTINEL
    ]
    forwarded_args.append(ELEVATION_SENTINEL)

    parameters = forwarded_args if is_frozen_app else [current_script, *forwarded_args]
    return current_executable, subprocess.list2cmdline(parameters)


def request_elevation() -> ElevationResult:
    """Ask Windows to relaunch the current process with administrator privileges."""
    executable, parameters = build_elevated_invocation()
    shell_execute_result = int(
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            parameters,
            os.getcwd(),
            1,
        )
    )

    if shell_execute_result > 32:
        return ElevationResult.RELAUNCHED
    if shell_execute_result == 1223:
        return ElevationResult.CANCELLED
    return ElevationResult.FAILED


def ensure_admin(auto_elevate: bool, launched_from_elevated_restart: bool) -> ElevationResult:
    """Ensure the process is elevated or try to elevate it when allowed."""
    if is_running_as_admin():
        return ElevationResult.READY

    if launched_from_elevated_restart:
        return ElevationResult.FAILED

    if not auto_elevate:
        return ElevationResult.READY

    logging.info("检测到当前不是管理员权限，正在向系统申请管理员授权...")
    return request_elevation()
