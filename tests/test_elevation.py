from __future__ import annotations

import unittest

from iconfix.constants import ELEVATION_SENTINEL
from iconfix.elevation import build_elevated_invocation


class ElevationInvocationTests(unittest.TestCase):
    def test_python_script_invocation_preserves_arguments(self) -> None:
        executable, parameters = build_elevated_invocation(
            argv=["IconFix.py", "--all", "-path", r"D:\Steam Icons"],
            frozen=False,
            executable=r"C:\Python311\python.exe",
            script_path=r"D:\Projects\Python\IconFix\IconFix.py",
        )

        self.assertEqual(executable, r"C:\Python311\python.exe")
        self.assertTrue(parameters.startswith(r"D:\Projects\Python\IconFix\IconFix.py"))
        self.assertIn("--all", parameters)
        self.assertIn(ELEVATION_SENTINEL, parameters)

    def test_existing_sentinel_is_not_duplicated(self) -> None:
        _, parameters = build_elevated_invocation(
            argv=["IconFix.py", "--all", ELEVATION_SENTINEL],
            frozen=False,
            executable="python",
            script_path="IconFix.py",
        )

        self.assertEqual(parameters.count(ELEVATION_SENTINEL), 1)


if __name__ == "__main__":
    unittest.main()
