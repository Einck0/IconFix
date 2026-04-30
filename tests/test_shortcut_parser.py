from __future__ import annotations

from pathlib import Path
import unittest

from iconfix.shortcut import ShortcutParseError, parse_shortcut_text


class ShortcutParserTests(unittest.TestCase):
    def test_parse_valid_shortcut(self) -> None:
        content = "\n".join(
            [
                "[InternetShortcut]",
                "URL=steam://rungameid/123456",
                r"IconFile=C:\Games\Steam\appcache\librarycache\demo_icon.ico",
            ]
        )

        metadata = parse_shortcut_text(Path("demo.url"), content)

        self.assertEqual(metadata.steam_id, "123456")
        self.assertEqual(metadata.icon_name, "demo_icon.ico")

    def test_reject_non_steam_shortcut(self) -> None:
        content = "\n".join(
            [
                "[InternetShortcut]",
                "URL=https://example.com",
                r"IconFile=C:\Games\icon.ico",
            ]
        )

        with self.assertRaises(ShortcutParseError):
            parse_shortcut_text(Path("demo.url"), content)


if __name__ == "__main__":
    unittest.main()
